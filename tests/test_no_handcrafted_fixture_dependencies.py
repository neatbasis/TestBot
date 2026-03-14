from __future__ import annotations

from pathlib import Path

TARGET_TEST_MODULES = (
    Path("tests/test_eval_fixtures.py"),
    Path("tests/test_eval_runtime_parity.py"),
    Path("tests/test_history_packer.py"),
    Path("tests/test_log_schema_validation.py"),
    Path("tests/test_turn_analytics_aggregator.py"),
)

DENYLIST_PATH_SNIPPETS = (
    "tests/fixtures/candidate_sets.jsonl",
    "tests/fixtures/eval_runtime_parity_",
    "tests/fixtures/history_transcript_fixture.json",
    "tests/fixtures/log_schema/",
    "tests/fixtures/session_events_fixture.jsonl",
    "tests/fixtures/alignment_dimension_events_fixture.jsonl",
)

ALLOWLIST_HELPER_IMPORT_SNIPPETS = (
    "from tests.helpers.eval_case_builders import",
    "from tests.helpers.eval_runtime_parity_scenarios import",
    "from tests.helpers.history_transcripts import",
    "from tests.helpers.log_schema_samples import",
    "from tests.helpers.turn_analytics_events import",
)


def test_target_modules_do_not_reference_handcrafted_fixture_files() -> None:
    for module_path in TARGET_TEST_MODULES:
        source_text = module_path.read_text(encoding="utf-8")

        forbidden_matches = [
            snippet for snippet in DENYLIST_PATH_SNIPPETS if snippet in source_text
        ]
        assert not forbidden_matches, (
            f"{module_path} contains forbidden handcrafted fixture references: "
            f"{forbidden_matches}"
        )


def test_target_modules_use_allowlisted_helper_imports() -> None:
    for module_path in TARGET_TEST_MODULES:
        source_text = module_path.read_text(encoding="utf-8")
        assert any(snippet in source_text for snippet in ALLOWLIST_HELPER_IMPORT_SNIPPETS), (
            f"{module_path} should import fixture builders from helpers. "
            f"Expected one of: {ALLOWLIST_HELPER_IMPORT_SNIPPETS}"
        )
