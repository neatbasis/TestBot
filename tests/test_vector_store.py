from __future__ import annotations

import sys
from dataclasses import dataclass
from types import ModuleType
from unittest.mock import MagicMock

from langchain_core.documents import Document
import pytest

from testbot.vector_store import (
    ElasticsearchMemoryStore,
    InMemoryMemoryStore,
    PromotingMemoryStore,
    build_memory_store,
    normalize_memory_store_mode,
)


@dataclass
class FakeStore:
    docs: list[Document]

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
        if not self.docs:
            return []
        return [(d, 0.9) for d in self.docs[:k]]


def test_promoting_memory_store_queries_fallback_and_promotes() -> None:
    primary = FakeStore(docs=[])
    fallback = FakeStore(docs=[Document(id="1", page_content="known fact", metadata={"ts": "2026-01-01"})])
    store = PromotingMemoryStore(primary=primary, fallback=fallback, promote_top_k=1)

    hits = store.similarity_search_with_score("known", k=2)

    assert len(hits) == 1
    assert hits[0][0].id == "1"
    assert primary.docs
    assert primary.docs[0].metadata["promoted_from"] == "elasticsearch"


def test_promoting_memory_store_does_not_promote_when_primary_has_hits() -> None:
    primary = FakeStore(docs=[Document(id="primary-1", page_content="known", metadata={})])
    fallback = FakeStore(docs=[Document(id="fallback-1", page_content="unused", metadata={})])
    store = PromotingMemoryStore(primary=primary, fallback=fallback, promote_top_k=1)

    hits = store.similarity_search_with_score("known", k=2)

    assert [doc.id for doc, _ in hits] == ["primary-1"]
    assert [doc.id for doc in primary.docs] == ["primary-1"]


def test_promoting_memory_store_respects_promotion_limit_and_empty_fallback() -> None:
    primary = FakeStore(docs=[])
    fallback = FakeStore(
        docs=[
            Document(id="s1", page_content="one", metadata={"source_type": "calendar"}),
            Document(id="s2", page_content="two", metadata={"source_type": "calendar"}),
        ]
    )
    store = PromotingMemoryStore(primary=primary, fallback=fallback, promote_top_k=1)

    store.similarity_search_with_score("known", k=2)
    assert [doc.id for doc in primary.docs] == ["s1"]

    empty_fallback = FakeStore(docs=[])
    no_hit_store = PromotingMemoryStore(primary=FakeStore(docs=[]), fallback=empty_fallback, promote_top_k=2)
    assert no_hit_store.similarity_search_with_score("missing", k=2) == []


@pytest.fixture
def fake_elasticsearch_module(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    es_client = MagicMock()
    es_ctor = MagicMock(return_value=es_client)
    module = ModuleType("elasticsearch")
    module.Elasticsearch = es_ctor
    monkeypatch.setitem(sys.modules, "elasticsearch", module)
    return es_ctor, es_client


def test_elasticsearch_memory_store_raises_without_package(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "elasticsearch", None)

    with pytest.raises(RuntimeError, match="elasticsearch package is required"):
        ElasticsearchMemoryStore(embeddings=StubEmbeddings(), url="http://localhost:9200", index="cards")


def test_elasticsearch_memory_store_creates_index_with_embedding_dims(fake_elasticsearch_module: tuple[MagicMock, MagicMock]) -> None:
    _es_ctor, es_client = fake_elasticsearch_module
    es_client.indices.exists.return_value = False

    ElasticsearchMemoryStore(embeddings=StubEmbeddings(), url="http://localhost:9200", index="cards")

    es_client.indices.create.assert_called_once()
    mapping = es_client.indices.create.call_args.kwargs["mappings"]["properties"]["embedding"]
    assert mapping["dims"] == 2
    assert mapping["similarity"] == "cosine"


def test_elasticsearch_memory_store_add_documents_and_search_are_safe_for_edge_cases(
    fake_elasticsearch_module: tuple[MagicMock, MagicMock],
) -> None:
    _es_ctor, es_client = fake_elasticsearch_module
    es_client.indices.exists.return_value = True
    store = ElasticsearchMemoryStore(embeddings=StubEmbeddings(), url="http://localhost:9200", index="cards")

    store.add_documents([])
    es_client.bulk.assert_not_called()

    store.add_documents([Document(id="d1", page_content="alpha", metadata={"ts": "2026-01-01T00:00:00Z"})])
    operations = es_client.bulk.call_args.kwargs["operations"]
    assert operations[0] == {"index": {"_index": "cards", "_id": "d1"}}
    assert operations[1]["page_content"] == "alpha"

    es_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "doc-1",
                    "_score": None,
                    "_source": {"page_content": "fact", "metadata": {"source_uri": "calendar://work/1"}},
                },
                {"_source": {}},
            ]
        }
    }
    hits = store.similarity_search_with_score("fact", k=2)

    assert len(hits) == 2
    assert hits[0][0].id == "doc-1"
    assert hits[0][1] == 0.0
    assert hits[1][0].id == ""

def test_elasticsearch_memory_store_normalizes_and_validates_document_ids(
    fake_elasticsearch_module: tuple[MagicMock, MagicMock],
) -> None:
    _es_ctor, es_client = fake_elasticsearch_module
    es_client.indices.exists.return_value = True
    store = ElasticsearchMemoryStore(embeddings=StubEmbeddings(), url="http://localhost:9200", index="cards")

    store.add_documents([Document(id="  d1  ", page_content="alpha", metadata={})])
    operations = es_client.bulk.call_args.kwargs["operations"]
    assert operations[0] == {"index": {"_index": "cards", "_id": "d1"}}

    with pytest.raises(ValueError, match="invalid id: None"):
        store.add_documents([Document(id=None, page_content="missing", metadata={})])

    with pytest.raises(ValueError, match="invalid id"):
        store.add_documents([Document(id="   ", page_content="blank", metadata={})])


class StubEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2]


def test_normalize_memory_store_mode_supports_in_memory_aliases() -> None:
    assert normalize_memory_store_mode("in_memory") == "in_memory"
    assert normalize_memory_store_mode("inmemory") == "in_memory"


def test_build_memory_store_defaults_to_in_memory_adapter() -> None:
    store = build_memory_store(embeddings=StubEmbeddings(), mode="in_memory")

    assert isinstance(store, InMemoryMemoryStore)


def test_inmemory_memory_store_retrieval_exclusions_block_same_turn_docs() -> None:
    class _StubVectorStore:
        def __init__(self) -> None:
            self._docs = [
                Document(id="turn-user", page_content="just said this", metadata={"doc_id": "turn-user", "ts": "2026-03-10T10:00:00Z"}),
                Document(
                    id="turn-reflection",
                    page_content="reflection for this turn",
                    metadata={"doc_id": "turn-reflection", "source_doc_id": "turn-user", "turn_doc_id": "turn-user"},
                ),
                Document(id="older-memory", page_content="older memory", metadata={"doc_id": "older-memory", "ts": "2026-03-01T10:00:00Z"}),
            ]

        def add_documents(self, documents: list[Document]) -> None:
            self._docs.extend(documents)

        def similarity_search_with_score(self, _query: str, k: int = 4) -> list[tuple[Document, float]]:
            return [(doc, 0.9) for doc in self._docs[:k]]

    store = InMemoryMemoryStore(_StubVectorStore())

    hits = store.similarity_search_with_score(
        "memory",
        k=5,
        exclude_doc_ids={"turn-user", "turn-reflection"},
        exclude_source_ids={"turn-user"},
        exclude_turn_scoped_ids={"turn-user", "turn-reflection"},
    )

    assert [doc.id for doc, _score in hits] == ["older-memory"]


def test_elasticsearch_memory_store_search_includes_retrieval_hygiene_filters(
    fake_elasticsearch_module: tuple[MagicMock, MagicMock],
) -> None:
    _es_ctor, es_client = fake_elasticsearch_module
    es_client.indices.exists.return_value = True
    es_client.search.return_value = {"hits": {"hits": []}}
    store = ElasticsearchMemoryStore(embeddings=StubEmbeddings(), url="http://localhost:9200", index="cards")

    store.similarity_search_with_score(
        "fact",
        k=2,
        exclude_doc_ids={"turn-user", "turn-reflection"},
        exclude_source_ids={"turn-user"},
        exclude_turn_scoped_ids={"turn-user", "turn-reflection"},
    )

    bool_query = es_client.search.call_args.kwargs["query"]["script_score"]["query"]["bool"]
    assert bool_query["must"] == [{"match_all": {}}]
    assert {"ids": {"values": ["turn-reflection", "turn-user"]}} in bool_query["must_not"]
    assert {"terms": {"metadata.source_doc_id": ["turn-user"]}} in bool_query["must_not"]
