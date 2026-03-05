from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from testbot.source_connectors import SourceConnector, SourceItem
from testbot.vector_store import MemoryStore


@dataclass(frozen=True)
class SourceIngestResult:
    fetched_count: int
    stored_count: int
    next_cursor: str | None
    memory_documents: list[Document]
    evidence_documents: list[Document]


def _provenance_metadata(*, connector: SourceConnector, item: SourceItem) -> dict[str, str]:
    return {
        "source_type": connector.source_type,
        "source_uri": item.source_uri,
        "retrieved_at": item.retrieved_at,
        "trust_tier": item.trust_tier,
    }


def _canonical_memory_doc(normalized_doc: Document, *, provenance: dict[str, str]) -> Document:
    metadata = {
        **dict(normalized_doc.metadata),
        **provenance,
        "type": str(normalized_doc.metadata.get("type") or "memory"),
        "record_kind": "source_memory",
    }
    return Document(id=normalized_doc.id, page_content=normalized_doc.page_content, metadata=metadata)


def _canonical_evidence_doc(normalized_doc: Document, *, provenance: dict[str, str]) -> Document:
    metadata = {
        **dict(normalized_doc.metadata),
        **provenance,
        "type": "source_evidence",
        "record_kind": "source_evidence",
    }
    evidence_id = str(normalized_doc.id or normalized_doc.metadata.get("doc_id") or "")
    return Document(id=f"evidence::{evidence_id}" if evidence_id else None, page_content=normalized_doc.page_content, metadata=metadata)


class SourceIngestor:
    """Orchestrates source fetch -> normalize -> canonicalize -> ingest."""

    def __init__(self, *, connector: SourceConnector, memory_store: MemoryStore) -> None:
        self._connector = connector
        self._memory_store = memory_store

    def ingest_once(self, *, cursor: str | None = None, limit: int = 50) -> SourceIngestResult:
        fetched_items = self._connector.fetch(cursor=cursor, limit=limit)
        memory_documents: list[Document] = []
        evidence_documents: list[Document] = []

        for item in fetched_items:
            normalized_doc = self._connector.normalize(item)
            provenance = _provenance_metadata(connector=self._connector, item=item)
            memory_documents.append(_canonical_memory_doc(normalized_doc, provenance=provenance))
            evidence_documents.append(_canonical_evidence_doc(normalized_doc, provenance=provenance))

        documents_to_store = [*memory_documents, *evidence_documents]
        if documents_to_store:
            self._memory_store.add_documents(documents_to_store)

        next_cursor = self._connector.update_cursor(previous_cursor=cursor, fetched_items=fetched_items)
        return SourceIngestResult(
            fetched_count=len(fetched_items),
            stored_count=len(documents_to_store),
            next_cursor=next_cursor,
            memory_documents=memory_documents,
            evidence_documents=evidence_documents,
        )
