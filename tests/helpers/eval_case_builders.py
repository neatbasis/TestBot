from __future__ import annotations

from typing import Any

from testbot.eval_fixtures import cases_by_id


def _candidate_set_from_case(*, fixture_id: str, case_id: str, query: str) -> dict[str, Any]:
    case = cases_by_id()[case_id]
    return {
        "fixture_id": fixture_id,
        "query": query,
        "source_case_id": case_id,
        "expected_doc_id": case.expected_doc_id,
        "candidates": [dict(candidate) for candidate in case.candidates],
    }


def build_eval_case_candidate_sets() -> list[dict[str, Any]]:
    return [
        _candidate_set_from_case(
            fixture_id="candidate-set-sleep-followup",
            case_id="sleep-followup",
            query="slept 4 hours last night",
        ),
        _candidate_set_from_case(
            fixture_id="candidate-set-no-memory-match",
            case_id="no-memory-match",
            query="passport number",
        ),
    ]


def build_eval_case_candidate_sets_by_id() -> dict[str, dict[str, Any]]:
    return {fixture["fixture_id"]: fixture for fixture in build_eval_case_candidate_sets()}
