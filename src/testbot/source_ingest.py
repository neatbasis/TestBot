from __future__ import annotations

from dataclasses import dataclass
import hashlib

from testbot.ports import PortDocument
from testbot.source_connectors import SourceConnector, SourceItem
from testbot.vector_store import (
    MemoryStore,
    SOURCE_EVIDENCE_LANE,
    UTTERANCE_MEMORY_LANE,
    with_record_lane_metadata,
)


@dataclass(frozen=True)
class UtteranceMemoryRecord:
    document: PortDocument


@dataclass(frozen=True)
class SourceEvidenceRecord:
    document: PortDocument


@dataclass(frozen=True)
class SourceIngestResult:
    fetched_count: int
    stored_count: int
    next_cursor: str | None
    memory_documents: list[PortDocument]
    evidence_documents: list[PortDocument]


def _provenance_metadata(*, connector: SourceConnector, item: SourceItem) -> dict[str, str]:
    return {
        "source_type": connector.source_type,
        "source_uri": item.source_uri,
        "retrieved_at": item.retrieved_at,
        "trust_tier": item.trust_tier,
    }


def _canonical_memory_doc(normalized_doc: PortDocument, *, provenance: dict[str, str]) -> PortDocument:
    source_item_type = normalized_doc.metadata.get("type")
    metadata = with_record_lane_metadata(
        {
        **dict(normalized_doc.metadata),
        **provenance,
        },
        lane=UTTERANCE_MEMORY_LANE,
    )
    if source_item_type is not None:
        metadata["source_item_type"] = str(source_item_type)
    doc_id = _resolve_source_document_id(normalized_doc, provenance=provenance)
    return PortDocument(doc_id=doc_id, content=normalized_doc.content, metadata=metadata)


def _canonical_evidence_doc(normalized_doc: PortDocument, *, provenance: dict[str, str]) -> PortDocument:
    metadata = with_record_lane_metadata(
        {
        **dict(normalized_doc.metadata),
        **provenance,
        },
        lane=SOURCE_EVIDENCE_LANE,
    )
    base_id = _resolve_source_document_id(normalized_doc, provenance=provenance)
    return PortDocument(doc_id=f"evidence::{base_id}", content=normalized_doc.content, metadata=metadata)


def _resolve_source_document_id(normalized_doc: PortDocument, *, provenance: dict[str, str]) -> str:
    normalized_id = str(normalized_doc.doc_id or "").strip()
    if normalized_id:
        return normalized_id

    metadata_doc_id = str(normalized_doc.metadata.get("doc_id") or "").strip()
    if metadata_doc_id:
        return metadata_doc_id

    source_type = str(provenance.get("source_type") or "")
    source_uri = str(provenance.get("source_uri") or "")
    normalized_content = normalized_doc.content.strip()
    content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()[:16]
    deterministic = f"{source_type}|{source_uri}|{content_hash}"
    return f"derived::{hashlib.sha256(deterministic.encode('utf-8')).hexdigest()[:24]}"


class SourceIngestor:
    """Orchestrates source fetch -> normalize -> canonicalize -> ingest."""

    def __init__(self, *, connector: SourceConnector, memory_store: MemoryStore) -> None:
        self._connector = connector
        self._memory_store = memory_store

    def ingest_once(self, *, cursor: str | None = None, limit: int = 50) -> SourceIngestResult:
        fetched_items = self._connector.fetch(cursor=cursor, limit=limit)
        memory_documents: list[PortDocument] = []
        evidence_documents: list[PortDocument] = []

        for item in fetched_items:
            normalized_doc = self._connector.normalize(item)
            provenance = _provenance_metadata(connector=self._connector, item=item)
            memory_documents.append(UtteranceMemoryRecord(_canonical_memory_doc(normalized_doc, provenance=provenance)).document)
            evidence_documents.append(SourceEvidenceRecord(_canonical_evidence_doc(normalized_doc, provenance=provenance)).document)

        documents_to_store = [*memory_documents, *evidence_documents]
        if documents_to_store:
            self._memory_store.add_memory_records(documents_to_store)

        next_cursor = self._connector.update_cursor(previous_cursor=cursor, fetched_items=fetched_items)
        return SourceIngestResult(
            fetched_count=len(fetched_items),
            stored_count=len(documents_to_store),
            next_cursor=next_cursor,
            memory_documents=memory_documents,
            evidence_documents=evidence_documents,
        )
