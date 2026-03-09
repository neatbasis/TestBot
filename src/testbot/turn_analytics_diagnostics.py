from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

IGNORED_ROWS_WARNING_THRESHOLD = 0.5


@dataclass
class CoverageDiagnostics:
    input_rows_total: int
    recognized_analytics_rows: int
    ignored_non_analytics_rows: int
    turn_start_events: int
    ignored_event_counts: dict[str, int]
    warnings: list[str]


def build_coverage_diagnostics(rows: Iterable[dict[str, Any]], analytics_events: set[str]) -> CoverageDiagnostics:
    input_rows_total = 0
    recognized_analytics_rows = 0
    ignored_non_analytics_rows = 0
    turn_start_events = 0
    ignored_event_counts: dict[str, int] = {}

    for row in rows:
        input_rows_total += 1
        event = str(row.get("event") or "unknown")
        if event in analytics_events:
            recognized_analytics_rows += 1
            if event == "user_utterance_ingest":
                turn_start_events += 1
            continue

        ignored_non_analytics_rows += 1
        ignored_event_counts[event] = ignored_event_counts.get(event, 0) + 1

    warnings: list[str] = []
    ignored_ratio = (ignored_non_analytics_rows / input_rows_total) if input_rows_total else 0.0
    if input_rows_total and ignored_ratio > IGNORED_ROWS_WARNING_THRESHOLD:
        warnings.append(
            f"ignored_non_analytics_rows exceeds {IGNORED_ROWS_WARNING_THRESHOLD:.0%} threshold "
            f"({ignored_non_analytics_rows}/{input_rows_total})."
        )
    if input_rows_total > 0 and turn_start_events == 0:
        warnings.append("No turn_start_events detected in non-empty input; no turns can be aggregated.")

    return CoverageDiagnostics(
        input_rows_total=input_rows_total,
        recognized_analytics_rows=recognized_analytics_rows,
        ignored_non_analytics_rows=ignored_non_analytics_rows,
        turn_start_events=turn_start_events,
        ignored_event_counts=ignored_event_counts,
        warnings=warnings,
    )
