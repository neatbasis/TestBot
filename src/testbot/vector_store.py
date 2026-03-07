from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from typing import Protocol

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


class MemoryStore(Protocol):
    def add_documents(self, documents: list[Document]) -> None: ...

    def similarity_search_with_score(self, query: str, k: int = 4) -> list[tuple[Document, float]]: ...


MemoryBackend = Literal["in_memory", "elasticsearch", "hybrid"]
RecordKind = Literal["utterance_memory", "reflection_hypothesis", "promoted_context", "source_evidence"]
RecordType = RecordKind

RECORD_KIND_UTTERANCE_MEMORY: RecordKind = "utterance_memory"
RECORD_KIND_REFLECTION_HYPOTHESIS: RecordKind = "reflection_hypothesis"
RECORD_KIND_PROMOTED_CONTEXT: RecordKind = "promoted_context"
RECORD_KIND_SOURCE_EVIDENCE: RecordKind = "source_evidence"

RECORD_KINDS: tuple[RecordKind, ...] = (
    RECORD_KIND_UTTERANCE_MEMORY,
    RECORD_KIND_REFLECTION_HYPOTHESIS,
    RECORD_KIND_PROMOTED_CONTEXT,
    RECORD_KIND_SOURCE_EVIDENCE,
)


@dataclass(frozen=True)
class RecordLane:
    record_kind: RecordKind
    record_type: RecordType


UTTERANCE_MEMORY_LANE = RecordLane(RECORD_KIND_UTTERANCE_MEMORY, RECORD_KIND_UTTERANCE_MEMORY)
REFLECTION_HYPOTHESIS_LANE = RecordLane(RECORD_KIND_REFLECTION_HYPOTHESIS, RECORD_KIND_REFLECTION_HYPOTHESIS)
PROMOTED_CONTEXT_LANE = RecordLane(RECORD_KIND_PROMOTED_CONTEXT, RECORD_KIND_PROMOTED_CONTEXT)
SOURCE_EVIDENCE_LANE = RecordLane(RECORD_KIND_SOURCE_EVIDENCE, RECORD_KIND_SOURCE_EVIDENCE)


def is_valid_record_kind(value: str) -> bool:
    return value in RECORD_KINDS


def with_record_lane_metadata(metadata: dict[str, object], *, lane: RecordLane) -> dict[str, object]:
    return {
        **metadata,
        "record_kind": lane.record_kind,
        "type": lane.record_type,
    }


def normalize_memory_store_mode(mode: str) -> MemoryBackend:
    normalized = mode.strip().lower()
    if normalized in {"inmemory", "in_memory"}:
        return "in_memory"
    if normalized == "elasticsearch":
        return "elasticsearch"
    if normalized == "hybrid":
        return "hybrid"
    raise ValueError(f"Unsupported memory store mode: {mode}")


@dataclass
class InMemoryMemoryStore:
    """Adapter that keeps runtime typed against a narrow memory store contract."""

    store: InMemoryVectorStore

    def add_documents(self, documents: list[Document]) -> None:
        self.store.add_documents(documents)

    def similarity_search_with_score(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        return self.store.similarity_search_with_score(query, k=k)


class ElasticsearchMemoryStore:
    """Minimal Elasticsearch-backed vector store with deterministic index mapping.

    Requires the `elasticsearch` Python package and an index configured with a `dense_vector`
    field named `embedding`.
    """

    def __init__(self, *, embeddings: Embeddings, url: str, index: str) -> None:
        try:
            from elasticsearch import Elasticsearch
        except Exception as exc:  # pragma: no cover - dependency/environment specific
            raise RuntimeError("elasticsearch package is required for ElasticsearchMemoryStore") from exc

        self._es = Elasticsearch(url)
        self._embeddings = embeddings
        self._index = index
        self._ensure_index()

    def _ensure_index(self) -> None:
        if self._es.indices.exists(index=self._index):
            return
        dims = len(self._embeddings.embed_query("dimension probe"))
        self._es.indices.create(
            index=self._index,
            mappings={
                "properties": {
                    "page_content": {"type": "text"},
                    "metadata": {"type": "object", "enabled": True},
                    "embedding": {"type": "dense_vector", "dims": dims, "index": True, "similarity": "cosine"},
                }
            },
        )

    def add_documents(self, documents: list[Document]) -> None:
        if not documents:
            return
        ops: list[dict] = []
        vectors = self._embeddings.embed_documents([d.page_content for d in documents])
        for index, (doc, vector) in enumerate(zip(documents, vectors, strict=True)):
            normalized_id = self._normalize_document_id(doc, position=index)
            ops.append({"index": {"_index": self._index, "_id": normalized_id}})
            ops.append(
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                    "embedding": vector,
                }
            )
        self._es.bulk(operations=ops, refresh=True)

    def _normalize_document_id(self, doc: Document, *, position: int) -> str:
        raw_id = doc.id
        if raw_id is None:
            raise ValueError(f"Document at position {position} has invalid id: None")

        normalized_id = str(raw_id).strip()
        if not normalized_id:
            raise ValueError(f"Document at position {position} has invalid id: {raw_id!r}")
        return normalized_id

    def similarity_search_with_score(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        query_vector = self._embeddings.embed_query(query)
        res = self._es.search(
            index=self._index,
            size=k,
            query={
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_vector},
                    },
                }
            },
        )
        hits: list[tuple[Document, float]] = []
        for row in res.get("hits", {}).get("hits", []):
            src = row.get("_source", {})
            hits.append(
                (
                    Document(
                        id=str(row.get("_id") or ""),
                        page_content=str(src.get("page_content") or ""),
                        metadata=dict(src.get("metadata") or {}),
                    ),
                    float(row.get("_score") or 0.0),
                )
            )
        return hits


@dataclass
class PromotingMemoryStore:
    """Hybrid store that queries in-memory first and promotes fallback hits into memory.

    This keeps the existing architecture intact while adding persistent fallback retrieval.
    """

    primary: MemoryStore
    fallback: MemoryStore
    promote_top_k: int = 3

    def add_documents(self, documents: list[Document]) -> None:
        self.primary.add_documents(documents)
        self.fallback.add_documents(documents)

    def similarity_search_with_score(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        primary_hits = self.primary.similarity_search_with_score(query, k=k)
        if primary_hits:
            return primary_hits

        fallback_hits = self.fallback.similarity_search_with_score(query, k=k)
        if fallback_hits:
            promoted_docs: list[Document] = []
            for doc, _score in fallback_hits[: self.promote_top_k]:
                promoted_docs.append(
                    Document(
                        id=doc.id,
                        page_content=doc.page_content,
                        metadata={**doc.metadata, "promoted_from": "elasticsearch"},
                    )
                )
            self.primary.add_documents(promoted_docs)
        return fallback_hits


def build_memory_store(*, embeddings: Embeddings, mode: str, elasticsearch_url: str = "", elasticsearch_index: str = "") -> MemoryStore:
    backend = normalize_memory_store_mode(mode)
    in_memory = InMemoryMemoryStore(InMemoryVectorStore(embeddings))
    if backend == "in_memory":
        return in_memory
    if backend == "elasticsearch":
        return ElasticsearchMemoryStore(embeddings=embeddings, url=elasticsearch_url, index=elasticsearch_index)
    if backend == "hybrid":
        fallback = ElasticsearchMemoryStore(embeddings=embeddings, url=elasticsearch_url, index=elasticsearch_index)
        return PromotingMemoryStore(primary=in_memory, fallback=fallback)
    raise ValueError(f"Unsupported memory store mode: {mode}")
