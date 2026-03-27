"""Canonical startup source-ingestion execution owner.

Scope: one-shot startup ingestion execution used by CLI startup composition.
Background ingestion lifecycle and broader orchestration remain in legacy runtime
until later extraction passes.
"""

from __future__ import annotations

import sys
from typing import Callable

from testbot.observability.session_log import append_session_log as _append_session_log
from testbot.ports import MemoryStorePort
from testbot.source_connectors import (
    ArxivSourceConnector,
    FixtureSourceConnector,
    LocalMarkdownSourceConnector,
    SourceConnector,
    WikipediaSummarySourceConnector,
)
from testbot.source_ingest import SourceIngestor


SessionLogger = Callable[[str, dict[str, object]], None]


def build_source_connector(*, runtime: dict[str, object], append_session_log: SessionLogger) -> SourceConnector | None:
    if not bool(runtime.get("source_ingest_enabled", False)):
        return None

    connector_type = str(runtime.get("source_connector_type", "fixture")).strip().lower()
    if connector_type == "fixture":
        fixture_path = str(runtime.get("source_fixture_path") or "").strip()
        if not fixture_path:
            append_session_log("source_ingest_skipped", {"reason": "missing_fixture_path", "connector_type": connector_type})
            return None
        return FixtureSourceConnector.from_json_file(source_type="fixture", fixture_path=fixture_path)

    if connector_type in {"local_markdown", "markdown"}:
        markdown_path = str(runtime.get("source_markdown_path") or "").strip()
        if not markdown_path:
            append_session_log("source_ingest_skipped", {"reason": "missing_markdown_path", "connector_type": connector_type})
            return None
        return LocalMarkdownSourceConnector(markdown_path=markdown_path)

    if connector_type in {"wikipedia", "wiki"}:
        topic = str(runtime.get("source_wikipedia_topic") or "").strip()
        language = str(runtime.get("source_wikipedia_language") or "en").strip() or "en"
        if not topic:
            append_session_log("source_ingest_skipped", {"reason": "missing_wikipedia_topic", "connector_type": connector_type})
            return None
        return WikipediaSummarySourceConnector(topic=topic, language=language)

    if connector_type == "arxiv":
        query = str(runtime.get("source_arxiv_query") or "").strip()
        if not query:
            append_session_log("source_ingest_skipped", {"reason": "missing_arxiv_query", "connector_type": connector_type})
            return None
        return ArxivSourceConnector(query=query)

    append_session_log("source_ingest_skipped", {"reason": "unsupported_connector_type", "connector_type": connector_type})
    return None


def run_source_ingestion(
    *,
    runtime: dict[str, object],
    store: MemoryStorePort,
    append_session_log: SessionLogger = _append_session_log,
) -> None:
    connector = build_source_connector(runtime=runtime, append_session_log=append_session_log)
    if connector is None:
        return

    cursor = str(runtime.get("source_ingest_cursor")) if runtime.get("source_ingest_cursor") is not None else None
    limit = int(runtime.get("source_ingest_limit", 50))
    if cursor is not None and not cursor.isdigit():
        append_session_log("source_ingest_cursor_invalid", {"cursor": cursor, "fallback_cursor": None, "background": False})
        cursor = None

    ingestor = SourceIngestor(connector=connector, memory_store=store)
    try:
        result = ingestor.ingest_once(cursor=cursor, limit=limit)
    except Exception as exc:
        append_session_log(
            "source_ingest_failed",
            {
                "connector_type": str(runtime.get("source_connector_type", "")).strip().lower(),
                "source_type": connector.source_type,
                "cursor": cursor,
                "limit": limit,
                "exception_class": exc.__class__.__name__,
                "exception_message": str(exc),
                "background": False,
                "ingestion_request_id": "",
            },
        )
        print(
            "Warning: source ingestion failed at startup; continuing without ingested source documents.",
            file=sys.stderr,
        )
        return

    append_session_log(
        "source_ingest_completed",
        {
            "source_type": connector.source_type,
            "fetched_count": result.fetched_count,
            "stored_count": result.stored_count,
            "next_cursor": result.next_cursor,
            "memory_doc_ids": [str(doc.doc_id or "") for doc in result.memory_documents],
            "evidence_doc_ids": [str(doc.doc_id or "") for doc in result.evidence_documents],
            "background": False,
            "ingestion_request_id": "",
        },
    )


__all__ = ["build_source_connector", "run_source_ingestion"]
