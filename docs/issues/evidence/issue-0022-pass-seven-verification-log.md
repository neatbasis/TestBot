# ISSUE-0022 pass-seven verification log

Run date (UTC): 2026-03-17T15:56:51Z

## Surface 1: Base-ref resolution helpers
### Command: grep -n "def git_ref_exists" scripts/all_green_gate.py scripts/validate_issue_links.py scripts/validate_issues.py

### Command: grep -n "def git_ref_exists" scripts/governance_rules.py
120:def git_ref_exists(ref: str, *, repo_root: Path) -> bool:

### Command: grep -n "def resolve_best_effort_diff_base_ref" scripts/all_green_gate.py
209:def resolve_best_effort_diff_base_ref(base_ref: str) -> tuple[str | None, list[str]]:

### Command: grep -n "def resolve_exact_commit_traceability_base_ref" scripts/validate_issue_links.py
128:def resolve_exact_commit_traceability_base_ref(base_ref: str) -> tuple[str | None, list[str]]:

### Command: grep -n "def resolve_safe_changed_path_base_ref" scripts/validate_issues.py
93:def resolve_safe_changed_path_base_ref(base_ref: str) -> tuple[str | None, list[str]]:

### Command: grep -n "repo_root=REPO_ROOT" scripts/all_green_gate.py scripts/validate_issue_links.py scripts/validate_issues.py
scripts/all_green_gate.py:213:        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),
scripts/validate_issue_links.py:132:        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),
scripts/validate_issues.py:97:        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),

### Command: ls tests/test_base_ref_policy_split.py
tests/test_base_ref_policy_split.py

### Command: python -m pytest tests/test_base_ref_policy_split.py -v
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /root/.pyenv/versions/3.11.14/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: anyio-4.12.1, langsmith-0.7.18
collecting ... collected 1 item

tests/test_base_ref_policy_split.py::test_base_ref_policy_split_between_diff_checks_and_commit_traceability PASSED [100%]

============================== 1 passed in 0.06s ===============================

## Surface 2: Changed-path skip policy
### Command: grep -n "GOVERNED_SURFACE_EXACT_PATHS\|GOVERNED_SURFACE_PATH_PREFIXES" scripts/all_green_gate.py
244:GOVERNED_SURFACE_EXACT_PATHS = {
256:GOVERNED_SURFACE_PATH_PREFIXES = (
311:            exact_paths=GOVERNED_SURFACE_EXACT_PATHS,
312:            prefixes=GOVERNED_SURFACE_PATH_PREFIXES,

### Command: grep -n "def apply_governance_skip_policy\|force_full_governance" scripts/all_green_gate.py
318:def apply_governance_skip_policy(
322:    force_full_governance: bool,
324:    if force_full_governance:
754:            force_full_governance=args.force_full_governance,

### Command: git log --oneline | grep -i "501\|governed\|skip"
9229ab0 Merge pull request #501 from neatbasis/codex/audit-round-trip-contract-tests-for-tightness
bfd8265 ISSUE-0022 Reconcile governed-surface skip override in all-green gate
b5ee103 docs(issues): add Issue State governed_execution to canonical issue records
fb6f275 ISSUE-0022 tighten changed-path skip-policy wording in checklist
c1f3624 Merge pull request #411 from neatbasis/codex/run-pytest-and-check-for-skipped-tests
0fc368f ISSUE-0013 Normalize live_smoke pytest collection and skip notices
9fe9479 ISSUE-0001 Guard identity recall from direct-answer retrieval skip

### Command: python -m pytest tests/test_all_green_gate.py -k "governed_surface or force_full_governance" -v
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /root/.pyenv/versions/3.11.14/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: anyio-4.12.1, langsmith-0.7.18
collecting ... collected 32 items / 27 deselected / 5 selected

tests/test_all_green_gate.py::test_apply_governance_skip_policy_runs_full_checks_for_governed_surface_change PASSED [ 20%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_governed_surface_override_dominates_mixed_changes PASSED [ 40%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_feature_status_yaml_does_not_force_full_governance PASSED [ 60%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_respects_force_full_governance PASSED [ 80%]
tests/test_all_green_gate.py::test_parse_args_supports_force_full_governance_flag PASSED [100%]

======================= 5 passed, 27 deselected in 0.13s =======================

### Command: python -m pytest tests/test_all_green_gate.py -v
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /root/.pyenv/versions/3.11.14/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: anyio-4.12.1, langsmith-0.7.18
collecting ... collected 32 items

tests/test_all_green_gate.py::test_main_fails_fast_when_behave_dependency_missing PASSED [  3%]
tests/test_all_green_gate.py::test_main_writes_behave_remediation_to_json_summary PASSED [  6%]
tests/test_all_green_gate.py::test_resolve_base_ref_falls_back_when_origin_main_missing PASSED [  9%]
tests/test_all_green_gate.py::test_resolve_base_ref_returns_canonical_note_when_no_refs_available PASSED [ 12%]
tests/test_all_green_gate.py::test_main_propagates_effective_base_ref_to_governance_checks_in_readiness_profile PASSED [ 15%]
tests/test_all_green_gate.py::test_build_checks_disables_turn_analytics_when_mode_off PASSED [ 18%]
tests/test_all_green_gate.py::test_build_checks_adds_optional_turn_analytics_checks PASSED [ 21%]
tests/test_all_green_gate.py::test_run_gate_marks_optional_failure_as_warning PASSED [ 25%]
tests/test_all_green_gate.py::test_run_gate_enforces_blocking_turn_analytics_checks PASSED [ 28%]
tests/test_all_green_gate.py::test_build_checks_includes_pipeline_stage_conformance_validator PASSED [ 31%]
tests/test_all_green_gate.py::test_build_checks_readiness_profile_has_expected_check_names PASSED [ 34%]
tests/test_all_green_gate.py::test_build_checks_triage_profile_excludes_governance_checks PASSED [ 37%]
tests/test_all_green_gate.py::test_build_checks_readiness_profile_has_no_duplicate_pytest_file_payloads PASSED [ 40%]
tests/test_all_green_gate.py::test_summarize_includes_stable_stage_rollups PASSED [ 43%]
tests/test_all_green_gate.py::test_parse_args_supports_default_json_output_path PASSED [ 46%]
tests/test_all_green_gate.py::test_extract_kpi_reason_classification_reads_structured_reason PASSED [ 50%]
tests/test_all_green_gate.py::test_summarize_includes_warning_reason_diagnostics PASSED [ 53%]
tests/test_all_green_gate.py::test_resolve_profile_defaults_to_triage_without_ci PASSED [ 56%]
tests/test_all_green_gate.py::test_resolve_profile_defaults_to_readiness_in_ci PASSED [ 59%]
tests/test_all_green_gate.py::test_summarize_groups_product_and_governance_failures PASSED [ 62%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_skips_issue_and_invariant_checks_when_irrelevant_changes PASSED [ 65%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_runs_full_checks_for_governed_surface_change PASSED [ 68%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_governed_surface_override_dominates_mixed_changes PASSED [ 71%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_feature_status_yaml_does_not_force_full_governance PASSED [ 75%]
tests/test_all_green_gate.py::test_apply_governance_skip_policy_respects_force_full_governance PASSED [ 78%]
tests/test_all_green_gate.py::test_run_gate_marks_skipped_checks_with_reason PASSED [ 81%]
tests/test_all_green_gate.py::test_summarize_includes_skipped_check_reasons PASSED [ 84%]
tests/test_all_green_gate.py::test_parse_args_supports_force_full_governance_flag PASSED [ 87%]
tests/test_all_green_gate.py::test_parse_args_supports_run_id PASSED     [ 90%]
tests/test_all_green_gate.py::test_write_verification_manifest_writes_expected_payload PASSED [ 93%]
tests/test_all_green_gate.py::test_parse_args_supports_post_triage_router_flags PASSED [ 96%]
tests/test_all_green_gate.py::test_maybe_run_triage_router_skips_without_summary_output PASSED [100%]

============================== 32 passed in 0.10s ==============================

## Surface 3: Issue status/state transition matrix
### Command: grep -n "ALLOWED_ISSUE_STATES\|ALLOWED_STATUS_VALUES\|ALLOWED_STATE_STATUS_TRANSITIONS" scripts/validate_issues.py
39:ALLOWED_ISSUE_STATES = {
44:ALLOWED_STATUS_VALUES = {
52:ALLOWED_STATE_STATUS_TRANSITIONS = {
54:    ISSUE_STATE_GOVERNED_EXECUTION: ALLOWED_STATUS_VALUES,
163:        if issue_state and issue_state not in ALLOWED_ISSUE_STATES:
164:            allowed = ", ".join(sorted(ALLOWED_ISSUE_STATES))
167:        if status and status not in ALLOWED_STATUS_VALUES:
168:            allowed = ", ".join(sorted(ALLOWED_STATUS_VALUES))
185:        if issue_state in ALLOWED_STATE_STATUS_TRANSITIONS and status in ALLOWED_STATUS_VALUES:
186:            allowed_state_statuses = ALLOWED_STATE_STATUS_TRANSITIONS[issue_state]

### Command: grep -n "parametrize.*status\|rejects_triage_intake_disallowed\|allows_governed_execution" tests/test_validate_issues.py
106:@pytest.mark.parametrize("status", ["open", "in_progress", "blocked", "resolved", "closed"])
107:def test_validate_issue_files_allows_governed_execution_status_transitions(
120:@pytest.mark.parametrize("status", ["in_progress", "blocked", "resolved", "closed"])
121:def test_validate_issue_files_rejects_triage_intake_disallowed_statuses(

### Command: python -m pytest tests/test_validate_issues.py -v
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /root/.pyenv/versions/3.11.14/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: anyio-4.12.1, langsmith-0.7.18
collecting ... collected 15 items

tests/test_validate_issues.py::test_resolve_base_ref_uses_canonical_missing_origin_note PASSED [  6%]
tests/test_validate_issues.py::test_validate_issue_files_accepts_triage_intake_minimal_schema PASSED [ 13%]
tests/test_validate_issues.py::test_validate_issue_files_allows_governed_execution_status_transitions[open] PASSED [ 20%]
tests/test_validate_issues.py::test_validate_issue_files_allows_governed_execution_status_transitions[in_progress] PASSED [ 26%]
tests/test_validate_issues.py::test_validate_issue_files_allows_governed_execution_status_transitions[blocked] PASSED [ 33%]
tests/test_validate_issues.py::test_validate_issue_files_allows_governed_execution_status_transitions[resolved] PASSED [ 40%]
tests/test_validate_issues.py::test_validate_issue_files_allows_governed_execution_status_transitions[closed] PASSED [ 46%]
tests/test_validate_issues.py::test_validate_issue_files_rejects_triage_intake_disallowed_statuses[in_progress] PASSED [ 53%]
tests/test_validate_issues.py::test_validate_issue_files_rejects_triage_intake_disallowed_statuses[blocked] PASSED [ 60%]
tests/test_validate_issues.py::test_validate_issue_files_rejects_triage_intake_disallowed_statuses[resolved] PASSED [ 66%]
tests/test_validate_issues.py::test_validate_issue_files_rejects_triage_intake_disallowed_statuses[closed] PASSED [ 73%]
tests/test_validate_issues.py::test_validate_issue_files_rejects_invalid_status_value PASSED [ 80%]
tests/test_validate_issues.py::test_validate_issue_files_rejects_invalid_issue_state_value PASSED [ 86%]
tests/test_validate_issues.py::test_validate_pr_body_uses_shared_metadata_issue_reference_primitive PASSED [ 93%]
tests/test_validate_issues.py::test_validate_issue_files_uses_shared_missing_canonical_sections_primitive PASSED [100%]

============================== 15 passed in 0.08s ==============================

## Surface 4: Integration proof
### Command: cat tests/test_base_ref_policy_split.py
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


all_green_gate = _load_module("all_green_gate", _SCRIPTS_DIR / "all_green_gate.py")
validate_issue_links = _load_module("validate_issue_links", _SCRIPTS_DIR / "validate_issue_links.py")


def test_base_ref_policy_split_between_diff_checks_and_commit_traceability() -> None:
    """Diff-oriented checks accept fallback refs while commit traceability fails closed."""
    readiness_checks = all_green_gate.build_checks(base_ref="HEAD~1", profile="readiness")
    issue_link_check = next(check for check in readiness_checks if check.name == "qa_validate_issue_links")

    assert issue_link_check.command[-1] == "HEAD~1"

    failures: list[validate_issue_links.ValidationFailure] = []
    allowed = validate_issue_links.commit_traceability_requires_exact_base_ref(
        requested_base_ref="origin/main",
        effective_base_ref="HEAD~1",
        allow_degraded_commit_traceability=False,
        failures=failures,
    )

    assert allowed is False
    assert failures
    assert "fail closed" in failures[0].message

### Command: grep -n "def commit_traceability_requires_exact_base_ref" scripts/validate_issue_links.py
255:def commit_traceability_requires_exact_base_ref(

### Command: grep -n "allow_degraded_commit_traceability" scripts/validate_issue_links.py
259:    allow_degraded_commit_traceability: bool,
271:    if requested_base_ref == effective_base_ref or allow_degraded_commit_traceability:
475:        allow_degraded_commit_traceability=args.allow_degraded_commit_traceability,

### Command: python -m pytest tests/test_base_ref_policy_split.py tests/test_validate_issue_links.py -v -k "policy_split or commit_traceability"
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /root/.pyenv/versions/3.11.14/bin/python
cachedir: .pytest_cache
rootdir: /workspace/TestBot
configfile: pyproject.toml
plugins: anyio-4.12.1, langsmith-0.7.18
collecting ... collected 15 items / 11 deselected / 4 selected

tests/test_base_ref_policy_split.py::test_base_ref_policy_split_between_diff_checks_and_commit_traceability PASSED [ 25%]
tests/test_validate_issue_links.py::test_commit_traceability_fails_closed_when_fallback_ref_is_used PASSED [ 50%]
tests/test_validate_issue_links.py::test_commit_traceability_can_opt_in_to_degraded_mode PASSED [ 75%]
tests/test_validate_issue_links.py::test_commit_traceability_failure_message_mentions_requested_and_effective_refs PASSED [100%]

======================= 4 passed, 11 deselected in 0.12s =======================
