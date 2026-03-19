from __future__ import annotations

from dataclasses import asdict

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.ports import MemorySearchQuery, PortDocument, ScoredPortDocument
from testbot.sat_chatbot_memory_v2 import stage_retrieve
from testbot.source_connectors import FixtureSourceConnector, LocalMarkdownSourceConnector, SourceItem
from testbot.vector_store import InMemoryMemoryStore, PromotingMemoryStore


class _StubVectorBackend:
    def __init__(self) -> None:
        self.docs: list[Document] = []

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4):
        del query
        return [(doc, 0.75) for doc in self.docs[:k]]


class _SearchOnlyPortStore:
    def __init__(self) -> None:
        self.last_query: MemorySearchQuery | None = None

    def search_memory_records(self, query: MemorySearchQuery) -> list[ScoredPortDocument]:
        self.last_query = query
        return [
            ScoredPortDocument(
                document=PortDocument(
                    doc_id="mem-1",
                    content="type: user_utterance\ntext: hello",
                    metadata={"doc_id": "mem-1", "record_kind": "utterance_memory"},
                ),
                score=0.9,
            )
        ]


def test_in_memory_adapter_exposes_port_dto_contract() -> None:
    adapter = InMemoryMemoryStore(store=_StubVectorBackend())

    adapter.add_memory_records([PortDocument(doc_id="d1", content="hello", metadata={"doc_id": "d1"})])
    hits = adapter.search_memory_records(MemorySearchQuery(query="hello", k=1))

    assert len(hits) == 1
    assert hits[0].document.doc_id == "d1"
    assert hits[0].document.content == "hello"
    assert isinstance(asdict(hits[0]), dict)


def test_promoting_store_contract_is_stable_across_adapter_swaps() -> None:
    primary = InMemoryMemoryStore(store=_StubVectorBackend())
    fallback = InMemoryMemoryStore(store=_StubVectorBackend())
    fallback.add_memory_records([PortDocument(doc_id="fallback-1", content="fallback", metadata={"doc_id": "fallback-1"})])

    store = PromotingMemoryStore(primary=primary, fallback=fallback, promote_top_k=1)
    hits = store.search_memory_records(MemorySearchQuery(query="fallback", k=1))

    assert hits and hits[0].document.doc_id == "fallback-1"
    assert hits[0].document.metadata["doc_id"] == "fallback-1"


def test_source_connector_contract_returns_port_documents(tmp_path) -> None:
    fixture_connector = FixtureSourceConnector(
        source_type="fixture",
        fixtures=(
            SourceItem(
                item_id="src-1",
                content="fixture content",
                source_uri="fixture://src-1",
                retrieved_at="2026-03-01T00:00:00Z",
                trust_tier="verified",
                metadata={"topic": "fixture"},
            ),
        ),
    )
    fixture_doc = fixture_connector.normalize(fixture_connector.fetch(cursor=None, limit=1)[0])

    note = tmp_path / "note.md"
    note.write_text("# Note\n\nText", encoding="utf-8")
    markdown_connector = LocalMarkdownSourceConnector(markdown_path=str(note))
    markdown_doc = markdown_connector.normalize(markdown_connector.fetch(cursor=None, limit=1)[0])

    assert isinstance(fixture_doc, PortDocument)
    assert isinstance(markdown_doc, PortDocument)
    assert fixture_doc.metadata["source_type"] == "fixture"
    assert markdown_doc.metadata["source_type"] == "local_markdown"


def test_stage_retrieve_uses_port_query_and_dto_boundary() -> None:
    store = _SearchOnlyPortStore()
    state = PipelineState(user_input="hello", rewritten_query="hello")

    _, docs_and_scores = stage_retrieve(store, state)

    assert store.last_query == MemorySearchQuery(query="hello", k=18)
    assert docs_and_scores[0][0].id == "mem-1"
