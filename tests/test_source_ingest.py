from __future__ import annotations

import json

import pytest
from langchain_core.documents import Document

from testbot.source_connectors import ArxivSourceConnector, LocalMarkdownSourceConnector, SourceItem, WikipediaSummarySourceConnector
from testbot.source_ingest import SourceIngestor


class _FakeConnector:
    source_type = "calendar"

    def __init__(self) -> None:
        self.cursor_updates: list[str | None] = []

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        if limit <= 0:
            return []
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


class _ChangingRetrievedAtMissingIdConnector(_FakeConnector):
    def __init__(self) -> None:
        super().__init__()
        self._retrieved_at_values = ["2026-03-05T09:30:00Z", "2026-03-05T10:00:00Z"]
        self._fetch_count = 0

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        del cursor, limit
        index = min(self._fetch_count, len(self._retrieved_at_values) - 1)
        self._fetch_count += 1
        return [
            SourceItem(
                item_id="evt-x",
                content="Team sync moved.",
                source_uri="calendar://work/evt-x",
                retrieved_at=self._retrieved_at_values[index],
                trust_tier="verified",
                metadata={"ts": "2026-03-06T11:00:00Z"},
            )
        ]

    def normalize(self, item: SourceItem) -> Document:
        return Document(id=None, page_content=item.content, metadata={"ts": item.metadata["ts"]})


class _TypedNormalizeConnector(_FakeConnector):
    def normalize(self, item: SourceItem) -> Document:
        return Document(
            id=item.item_id,
            page_content=item.content,
            metadata={"ts": item.metadata["ts"], "doc_id": item.item_id, "type": "calendar_event"},
        )


class _FakeStore:
    def __init__(self) -> None:
        self.docs: list[Document] = []

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4):  # pragma: no cover
        del query, k
        return []


class _FailingStore:
    def add_documents(self, documents: list[Document]) -> None:
        del documents
        raise RuntimeError("embedding backend unavailable")


def test_source_ingestor_propagates_store_add_documents_failures() -> None:
    connector = _FakeConnector()
    ingestor = SourceIngestor(connector=connector, memory_store=_FailingStore())

    with pytest.raises(RuntimeError, match="embedding backend unavailable"):
        ingestor.ingest_once(cursor=None)


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
    assert result.memory_documents[0].metadata["type"] == "memory"
    assert result.evidence_documents[0].metadata["record_kind"] == "source_evidence"
    assert result.evidence_documents[0].metadata["type"] == "source_evidence"
    assert result.evidence_documents[0].metadata["source_type"] == "calendar"
    assert len(store.docs) == 2


def test_source_ingestor_memory_type_is_not_overridden_by_connector_item_type() -> None:
    connector = _TypedNormalizeConnector()
    store = _FakeStore()
    ingestor = SourceIngestor(connector=connector, memory_store=store)

    result = ingestor.ingest_once(cursor=None)

    assert len(result.memory_documents) == 1
    assert len(result.evidence_documents) == 1
    assert result.memory_documents[0].metadata["type"] == "memory"
    assert result.memory_documents[0].metadata["source_item_type"] == "calendar_event"
    assert result.evidence_documents[0].metadata["type"] == "source_evidence"
    assert result.memory_documents[0].metadata["record_kind"] == "source_memory"
    assert result.evidence_documents[0].metadata["record_kind"] == "source_evidence"
    assert [doc.metadata["record_kind"] for doc in store.docs] == ["source_memory", "source_evidence"]


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


def test_source_ingestor_derived_ids_ignore_retrieved_at_for_unchanged_content() -> None:
    connector = _ChangingRetrievedAtMissingIdConnector()
    store = _FakeStore()
    ingestor = SourceIngestor(connector=connector, memory_store=store)

    first = ingestor.ingest_once(cursor=None)
    second = ingestor.ingest_once(cursor=None)

    assert first.memory_documents[0].metadata["retrieved_at"] != second.memory_documents[0].metadata["retrieved_at"]
    assert first.memory_documents[0].id == second.memory_documents[0].id
    assert first.evidence_documents[0].id == second.evidence_documents[0].id


def test_source_item_requires_mandatory_provenance_fields() -> None:
    with pytest.raises(ValueError):
        SourceItem(
            item_id="evt-1",
            content="Project review",
            source_uri="",
            retrieved_at="2026-03-05T09:00:00Z",
            trust_tier="verified",
            metadata={},
        )

    with pytest.raises(ValueError):
        SourceItem(
            item_id="evt-1",
            content="Project review",
            source_uri="calendar://work/evt-1",
            retrieved_at="",
            trust_tier="verified",
            metadata={},
        )

    with pytest.raises(ValueError):
        SourceItem(
            item_id="evt-1",
            content="Project review",
            source_uri="calendar://work/evt-1",
            retrieved_at="2026-03-05T09:00:00Z",
            trust_tier="",
            metadata={},
        )


def test_source_ingestor_respects_zero_limit() -> None:
    connector = _FakeConnector()
    store = _FakeStore()
    ingestor = SourceIngestor(connector=connector, memory_store=store)

    result = ingestor.ingest_once(cursor=None, limit=0)

    assert result.fetched_count == 0
    assert result.stored_count == 0
    assert result.next_cursor is None
    assert connector.cursor_updates == [None]
    assert store.docs == []


def test_source_ingestor_respects_negative_limit() -> None:
    connector = _FakeConnector()
    store = _FakeStore()
    ingestor = SourceIngestor(connector=connector, memory_store=store)

    result = ingestor.ingest_once(cursor=None, limit=-2)

    assert result.fetched_count == 0
    assert result.stored_count == 0
    assert result.next_cursor is None
    assert connector.cursor_updates == [None]
    assert store.docs == []


def test_source_ingestor_local_markdown_connector_integration(tmp_path) -> None:
    note = tmp_path / "operator.md"
    note.write_text("# Operator canon\n\nUse explicit provenance.", encoding="utf-8")
    store = _FakeStore()
    ingestor = SourceIngestor(connector=LocalMarkdownSourceConnector(markdown_path=str(note)), memory_store=store)

    result = ingestor.ingest_once(cursor=None)

    assert result.fetched_count == 1
    assert result.stored_count == 2
    assert result.next_cursor == "1"
    assert result.evidence_documents[0].metadata["source_type"] == "local_markdown"
    assert result.evidence_documents[0].metadata["trust_tier"] == "operator"


def test_source_ingestor_wikipedia_connector_integration() -> None:
    payload = {
        "title": "OpenAI",
        "extract": "OpenAI is an AI research lab.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/OpenAI"}},
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

    store = _FakeStore()
    ingestor = SourceIngestor(
        connector=WikipediaSummarySourceConnector(topic="OpenAI", opener=lambda *args, **kwargs: _Response()),
        memory_store=store,
    )

    result = ingestor.ingest_once(cursor=None)

    assert result.fetched_count == 1
    assert result.stored_count == 2
    assert result.next_cursor == "done"
    assert result.evidence_documents[0].metadata["source_type"] == "wikipedia"
    assert result.evidence_documents[0].metadata["source_uri"] == "https://en.wikipedia.org/wiki/OpenAI"
    assert result.evidence_documents[0].metadata["trust_tier"] == "community"


def test_source_ingestor_arxiv_connector_integration(monkeypatch) -> None:
    xml_payload = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <id>http://arxiv.org/abs/1234.5678v1</id>
    <updated>2026-03-01T12:00:00Z</updated>
    <title>Useful Paper</title>
    <summary>We show deterministic testing.</summary>
    <author><name>Ada Lovelace</name></author>
  </entry>
</feed>
"""

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def read(self) -> bytes:
            return xml_payload.encode("utf-8")

    monkeypatch.setattr("testbot.source_connectors.urlopen", lambda *args, **kwargs: _Response())

    store = _FakeStore()
    ingestor = SourceIngestor(connector=ArxivSourceConnector(query="cat:cs.AI"), memory_store=store)

    result = ingestor.ingest_once(cursor=None)

    assert result.fetched_count == 1
    assert result.stored_count == 2
    assert result.next_cursor == "1"
    assert result.evidence_documents[0].metadata["source_type"] == "arxiv"
    assert result.evidence_documents[0].metadata["source_uri"] == "http://arxiv.org/abs/1234.5678v1"
    assert result.evidence_documents[0].metadata["trust_tier"] == "preprint"
