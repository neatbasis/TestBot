from __future__ import annotations

import json

from testbot.source_ingestion_startup import run_source_ingestion


class _Store:
    def add_memory_records(self, records):
        del records


def test_startup_ingestion_skip_logs_reason_when_connector_config_missing(tmp_path) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    run_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": "",
        },
        store=_Store(),
        append_session_log=lambda event, payload: events.append((event, payload)),
    )

    assert events == [
        (
            "source_ingest_skipped",
            {"reason": "missing_fixture_path", "connector_type": "fixture"},
        )
    ]


def test_startup_ingestion_failure_logs_non_fatal_payload(monkeypatch, tmp_path, capsys) -> None:
    fixture_path = tmp_path / "source_fixture.json"
    fixture_path.write_text(
        json.dumps([
            {
                "item_id": "src-1",
                "content": "A Hilbert space is complete.",
                "source_uri": "fixture://wiki/hilbert-space",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": "verified",
                "metadata": {"ts": "2026-03-10T09:00:00Z"},
            }
        ]),
        encoding="utf-8",
    )

    class _FailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise RuntimeError("boom")

    monkeypatch.setattr("testbot.source_ingestion_startup.SourceIngestor", _FailingIngestor)
    events: list[tuple[str, dict[str, object]]] = []

    run_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 5,
            "source_ingest_cursor": "12",
        },
        store=_Store(),
        append_session_log=lambda event, payload: events.append((event, payload)),
    )

    captured = capsys.readouterr()
    assert "continuing without ingested source documents" in captured.err
    assert events[-1][0] == "source_ingest_failed"
    assert events[-1][1]["background"] is False


def test_startup_ingestion_completion_logs_expected_shape(tmp_path) -> None:
    fixture_path = tmp_path / "source_fixture.json"
    fixture_path.write_text(
        json.dumps([
            {
                "item_id": "src-1",
                "content": "A Hilbert space is complete.",
                "source_uri": "fixture://wiki/hilbert-space",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": "verified",
                "metadata": {"ts": "2026-03-10T09:00:00Z"},
            }
        ]),
        encoding="utf-8",
    )

    events: list[tuple[str, dict[str, object]]] = []
    run_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 10,
        },
        store=_Store(),
        append_session_log=lambda event, payload: events.append((event, payload)),
    )

    assert events[-1][0] == "source_ingest_completed"
    completion = events[-1][1]
    assert completion["background"] is False
    assert completion["ingestion_request_id"] == ""
    assert completion["stored_count"] == 2
