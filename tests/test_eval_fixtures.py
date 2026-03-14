from __future__ import annotations

from testbot.eval_fixtures import best_candidate_doc_id, cases_by_id, is_iso_timestamp
from tests.helpers.eval_case_builders import build_eval_case_candidate_sets
from tests.helpers.eval_runtime_parity_scenarios import runtime_parity_scenarios


def test_eval_cases_have_fixed_timestamps_and_expected_doc_ids() -> None:
    for case in cases_by_id().values():
        for candidate in case.candidates:
            assert is_iso_timestamp(candidate["ts"])
        assert best_candidate_doc_id(case) == case.expected_doc_id


def test_candidate_set_fixtures_track_eval_cases() -> None:
    case_index = cases_by_id()

    for fixture in build_eval_case_candidate_sets():
        source_case = case_index[fixture["source_case_id"]]
        expected_doc_id = fixture["expected_doc_id"]
        assert expected_doc_id == source_case.expected_doc_id
        assert all(is_iso_timestamp(candidate["ts"]) for candidate in fixture["candidates"])


def test_eval_runtime_parity_fixture_sets_have_fixed_timestamps() -> None:
    for scenario in runtime_parity_scenarios():
        assert scenario.family
        assert scenario.expected["intent"] in {"memory-grounded", "dont-know"}
        assert all((not candidate.get("ts")) or is_iso_timestamp(candidate["ts"]) for candidate in scenario.candidates)
