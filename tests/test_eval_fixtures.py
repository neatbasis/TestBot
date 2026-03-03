from __future__ import annotations

import json
from pathlib import Path

from testbot.eval_fixtures import best_candidate_doc_id, cases_by_id, is_iso_timestamp


def test_eval_cases_have_fixed_timestamps_and_expected_doc_ids() -> None:
    for case in cases_by_id().values():
        for candidate in case.candidates:
            assert is_iso_timestamp(candidate["ts"])
        assert best_candidate_doc_id(case) == case.expected_doc_id


def test_candidate_set_fixtures_track_eval_cases() -> None:
    fixtures_path = Path("tests/fixtures/candidate_sets.jsonl")
    case_index = cases_by_id()

    with fixtures_path.open("r", encoding="utf-8") as fixture_file:
        for line in fixture_file:
            fixture = json.loads(line)
            source_case = case_index[fixture["source_case_id"]]
            expected_doc_id = fixture["expected_doc_id"]
            assert expected_doc_id == source_case.expected_doc_id
            assert all(is_iso_timestamp(candidate["ts"]) for candidate in fixture["candidates"])
