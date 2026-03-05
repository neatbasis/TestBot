from __future__ import annotations

from langchain_core.documents import Document

from testbot.source_connectors import SourceItem
from testbot.source_ingest import SourceIngestor


class _FakeConnector:
    source_type = "calendar"

    def __init__(self) -> None:
        self.cursor_updates: list[str | None] = []

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        del limit
        if cursor == "end":
            return []
        return [
            SourceItem(
                item_id="evt-1",
                content="Project review at 10:00.",
                source_uri="calendar://work/evt-1",
                retrieved_at="2026-03-05T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-06T10:00:00Z", "doc_id": "evt-1"},
            )
        ]

    def normalize(self, item: SourceItem) -> Document:
        return Document(id=item.item_id, page_content=item.content, metadata={"ts": item.metadata["ts"], "doc_id": item.item_id})

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None:
        self.cursor_updates.append(previous_cursor)
        return "end" if fetched_items else previous_cursor


class _MissingIdConnector(_FakeConnector):
    def __init__(self) -> None:
        super().__init__()
        self._item = SourceItem(
            item_id="evt-x",
            content="Team sync moved.",
            source_uri="calendar://work/evt-x",
            retrieved_at="2026-03-05T09:30:00Z",
            trust_tier="verified",
            metadata={"ts": "2026-03-06T11:00:00Z"},
        )

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        del cursor, limit
        return [self._item]

    def normalize(self, item: SourceItem) -> Document:
        del item
        return Document(id=None, page_content=self._item.content, metadata={"ts": self._item.metadata["ts"]})


class _FakeStore:
    def __init__(self) -> None:
        self.docs: list[Document] = []

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4):  # pragma: no cover
        del query, k
        return []


def test_source_ingestor_stores_memory_and_evidence_with_provenance() -> None:
    connector = _FakeConnector()
    store = _FakeStore()
    ingestor = SourceIngestor(connector=connector, memory_store=store)

    result = ingestor.ingest_once(cursor=None)

    assert result.fetched_count == 1
    assert result.stored_count == 2
    assert result.next_cursor == "end"
    assert len(result.memory_documents) == 1
    assert len(result.evidence_documents) == 1
    assert result.evidence_documents[0].metadata["record_kind"] == "source_evidence"
    assert result.evidence_documents[0].metadata["source_type"] == "calendar"
    assert len(store.docs) == 2


def test_source_ingestor_derives_stable_ids_when_normalized_id_and_doc_id_are_missing() -> None:
    connector = _MissingIdConnector()
    store = _FakeStore()
    ingestor = SourceIngestor(connector=connector, memory_store=store)

    first = ingestor.ingest_once(cursor=None)
    second = ingestor.ingest_once(cursor=None)

    memory_id = first.memory_documents[0].id
    evidence_id = first.evidence_documents[0].id

    assert memory_id
    assert evidence_id
    assert memory_id == second.memory_documents[0].id
    assert evidence_id == second.evidence_documents[0].id
    assert evidence_id == f"evidence::{memory_id}"
    assert len(store.docs) == 4
