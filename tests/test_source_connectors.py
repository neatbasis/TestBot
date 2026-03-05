from __future__ import annotations

import json

from testbot.source_connectors import FixtureSourceConnector, SourceItem
from testbot.source_ingest import SourceIngestor


class _FakeStore:
    def __init__(self) -> None:
        self.docs = []

    def add_documents(self, documents):
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4):  # pragma: no cover
        del query, k
        return []


def test_fixture_connector_fetch_normalize_and_cursor_lifecycle() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
            SourceItem(
                item_id="evt-2",
                content="Retrospective at 15:00.",
                source_uri="calendar://team/evt-2",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T15:00:00Z"},
            ),
        ),
    )

    first_batch = connector.fetch(cursor=None, limit=1)
    assert [item.item_id for item in first_batch] == ["evt-1"]

    normalized = connector.normalize(first_batch[0])
    assert normalized.id == "evt-1"
    assert normalized.metadata["doc_id"] == "evt-1"
    assert normalized.metadata["source_uri"] == "calendar://team/evt-1"

    cursor = connector.update_cursor(previous_cursor=None, fetched_items=first_batch)
    assert cursor == "1"

    second_batch = connector.fetch(cursor=cursor, limit=2)
    assert [item.item_id for item in second_batch] == ["evt-2"]

    end_cursor = connector.update_cursor(previous_cursor=cursor, fetched_items=second_batch)
    assert end_cursor == "2"
    assert connector.fetch(cursor=end_cursor, limit=5) == []


def test_fixture_connector_fetch_returns_empty_for_zero_limit() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
        ),
    )


    assert connector.fetch(cursor=None, limit=0) == []


def test_fixture_connector_fetch_returns_empty_for_negative_limit() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
        ),
    )

    assert connector.fetch(cursor=None, limit=-3) == []


def test_fixture_connector_fetch_positive_limit_still_paginates() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-1",
                content="Morning sync at 09:30.",
                source_uri="calendar://team/evt-1",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T09:30:00Z"},
            ),
            SourceItem(
                item_id="evt-2",
                content="Retrospective at 15:00.",
                source_uri="calendar://team/evt-2",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T15:00:00Z"},
            ),
            SourceItem(
                item_id="evt-3",
                content="Planning at 16:00.",
                source_uri="calendar://team/evt-3",
                retrieved_at="2026-03-11T09:00:00Z",
                trust_tier="verified",
                metadata={"ts": "2026-03-11T16:00:00Z"},
            ),
        ),
    )

    assert [item.item_id for item in connector.fetch(cursor=None, limit=2)] == ["evt-1", "evt-2"]
    assert [item.item_id for item in connector.fetch(cursor="2", limit=2)] == ["evt-3"]


def test_source_ingest_canonicalizes_fixture_connector_docs() -> None:
    connector = FixtureSourceConnector(
        source_type="calendar",
        fixtures=(
            SourceItem(
                item_id="evt-3",
                content="Bill due Friday.",
                source_uri="calendar://finance/evt-3",
                retrieved_at="2026-03-12T08:15:00Z",
                trust_tier="high",
                metadata={"ts": "2026-03-13T10:00:00Z"},
            ),
        ),
    )
    store = _FakeStore()

    result = SourceIngestor(connector=connector, memory_store=store).ingest_once(cursor=None)

    assert result.fetched_count == 1
    assert result.stored_count == 2
    memory_doc = result.memory_documents[0]
    evidence_doc = result.evidence_documents[0]
    assert memory_doc.metadata["record_kind"] == "source_memory"
    assert evidence_doc.metadata["record_kind"] == "source_evidence"
    assert evidence_doc.metadata["source_type"] == "calendar"
    assert evidence_doc.metadata["trust_tier"] == "high"


def test_fixture_connector_can_load_json_fixture_file(tmp_path) -> None:
    fixture_path = tmp_path / "source_fixture.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "item_id": "src-1",
                    "content": "Task: utility bill due Friday",
                    "source_uri": "ha://tasks/utility-bill",
                    "retrieved_at": "2026-03-10T09:00:00Z",
                    "trust_tier": "medium",
                    "metadata": {"ts": "2026-03-14T00:00:00Z"},
                }
            ]
        ),
        encoding="utf-8",
    )

    connector = FixtureSourceConnector.from_json_file(source_type="home_automation", fixture_path=str(fixture_path))

    items = connector.fetch(cursor=None, limit=10)
    assert len(items) == 1
    assert items[0].item_id == "src-1"
    assert connector.normalize(items[0]).metadata["source_type"] == "home_automation"
