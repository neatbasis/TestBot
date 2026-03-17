diff --git a/docs/issues.md b/docs/issues.md
index 33e0ad7..cfc8072 100644
--- a/docs/issues.md
+++ b/docs/issues.md
@@ -70,6 +70,15 @@ Recommended metadata extension for linked issue streams:
 - `Canonical Cross-Reference` (optional but recommended when linked planning/implementation issues exist; use issue filename, e.g., `ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`).
 
 
+### Status/state enforcement matrix (canonical vs validator)
+
+| Issue State | Allowed `Status` values (canonical) | Transition/enforcement rule | Rejection cases (enforced by `scripts/validate_issues.py`) |
+| --- | --- | --- | --- |
+| `triage_intake` | `open` only | Must be promoted to `governed_execution` before any execution statuses (`in_progress`, `blocked`, `resolved`, `closed`). | Reject missing `Status`; reject any non-`open` status; reject invalid status values; reject invalid issue-state values. |
+| `governed_execution` | `open`, `in_progress`, `blocked`, `resolved`, `closed` | Full canonical schema applies; status must be one of the canonical lifecycle values. | Reject invalid status values (for example `paused`); reject invalid issue-state values. |
+
+Canonical reconciliation decision: **`docs/issues.md` is authoritative for status/state vocabulary and transition semantics; `scripts/validate_issues.py` and `tests/test_validate_issues.py` must enforce this table exactly.**
+
 ## Severity and Red-Tag area
 
 A **Red-Tag** issue is any issue with severity `red` and one or more of:
diff --git a/docs/issues/evidence/governance-stabilization-checklist.md b/docs/issues/evidence/governance-stabilization-checklist.md
index 1204766..26f15a3 100644
--- a/docs/issues/evidence/governance-stabilization-checklist.md
+++ b/docs/issues/evidence/governance-stabilization-checklist.md
@@ -28,8 +28,8 @@ Use this checklist to inventory current behavior, identify overlap/drift, choose
 
 | Surface | Canonical file(s) | Current status | Docs/tests agree? | Duplicate/conflict? | Canonical decision | Action needed | Done |
 | --- | --- | --- | --- | --- | --- | --- | --- |
-| Shared governance rules | `scripts/governance_rules.py` | decision made | partial (helper behavior is duplicated consistently across scripts, but tests currently validate per-script copies rather than one authoritative shared implementation path) | yes (`git_ref_exists` and `resolve_base_ref` are duplicated in `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py`; `git_ref_exists` shows no meaningful divergence, and `resolve_base_ref` differs only in caller-facing degraded-mode note wording) | **Canonical decision (analysis ratified):** centralize base-ref resolution primitives in `scripts/governance_rules.py`. Keep one shared behavioral implementation for `git_ref_exists` and `resolve_base_ref`; allow only thin caller wrappers if caller-specific note wording must remain different. | replace local helper implementations in `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py` with shared imports or thin wrappers; move duplicated helper tests toward direct shared-helper coverage plus minimal caller integration checks | ☐ |
-| Issue schema/state model | `docs/issues.md`, `scripts/validate_issues.py` | inventory complete | mostly yes for `triage_intake` / `governed_execution` and transition semantics | possible edge drift (status/state enforcement details may differ across docs/tests) | TBD | compare enforced transitions and allowed statuses in docs vs validator tests; record any mismatch as explicit reconcile item | ☐ |
+| Shared governance rules | `scripts/governance_rules.py` | reconciled | yes (base-ref helpers are centralized in `scripts/governance_rules.py`, and consumer-specific wrappers now make policy intent explicit: best-effort diff base, safe changed-path base, and exact-base-required commit-traceability) | resolved (shared git/ref primitives are centralized, while consumer-local policy wrappers remain intentional, explicit, and non-uniform by design) | **Canonical decision (implemented):** keep shared git/ref primitives in `scripts/governance_rules.py`, while preserving explicit consumer policy boundaries. Commit-traceability consumers must fail closed on degraded base-ref fallback by default; degraded mode is explicit opt-in only. | keep boundary-naming and policy tests synchronized as gate/validator call paths evolve | ☑ |
+| Issue schema/state model | `docs/issues.md`, `scripts/validate_issues.py` | verified | yes (status/state vocabulary and transition constraints are now explicitly codified in docs and validator/tests enforce the same matrix deterministically) | resolved | **Canonical decision (implemented):** `docs/issues.md` is authoritative; `scripts/validate_issues.py` enforces canonical issue states (`triage_intake`, `governed_execution`), canonical status set (`open`, `in_progress`, `blocked`, `resolved`, `closed`), and state-specific transition rule (`triage_intake` -> `open` only). Known non-blocking edge case: transition checks run after vocabulary validation, so a file with an invalid `Issue State` plus a valid-but-wrong `Status` may emit one rejection instead of both vocabulary and transition failures; rejection coverage is still preserved and remains freeze-contract compliant. | keep matrix/table and validator constants synchronized when lifecycle vocabulary changes | ☑ |
 | Issue-link / reference validation | `scripts/validate_issue_links.py` | inventory complete | partial (manifest-link and reference checks exist, but ownership boundary vs schema validator is not yet fully explicit) | likely (overlap with schema/state checks and manifest semantics) | TBD | document exact boundary: what link validator owns vs what issue-schema validator owns; eliminate ambiguity | ☐ |
 | RED_TAG derivation | `scripts/generate_red_tag_index.py`, `docs/issues/RED_TAG.md` | inventory complete | mostly yes on generated-file expectation and severity-driven derivation | possible (metadata coupling still needs explicit audit) | TBD | verify generated-only flow end-to-end, including validator expectations and no hand-edited policy drift | ☐ |
 | Gate profiles | `scripts/all_green_gate.py`, `docs/testing.md`, `README.md` | inventory complete | partial (triage/readiness semantics are documented but need consistency audit against gate implementation/tests) | likely (profile-local behavior vs shared governance check surfaces) | TBD | inventory profile behavior, ensure one canonical check path per profile, and reconcile docs/examples with implementation | ☐ |
@@ -37,7 +37,7 @@ Use this checklist to inventory current behavior, identify overlap/drift, choose
 | Feature-status / issue linkage | `docs/qa/feature-status.yaml`, `scripts/report_feature_status.py`, `scripts/suggest_issue_links.py` | inventory complete | partial (linkage contract exists; fallback/implicit behavior still needs conformance check) | possible (explicit linkage and suggestion fallback may overlap) | TBD | verify canonical linkage contract and document fallback precedence; align fixtures/examples if needed | ☐ |
 | Verification manifest semantics | `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `scripts/verification_manifest_contract.py`, `artifacts/verification/*` | verified | yes (single shared contract now defines producer payload shape + required checks and consumer interpretation/failure semantics) | resolved | **Canonical decision (authoritative contract):** producer (`all_green_gate.py`) MUST emit manifest payloads via `verification_manifest_contract.build_verification_manifest_payload` with canonical `required_checks`; consumer (`validate_issue_links.py`) MUST validate manifest reference path/run ID + payload semantics via `validate_manifest_payload_contract`, treating `run_id`, `required_checks`, and `checks[*].name` as authoritative, and MUST fail on missing/malformed `required_checks` or missing required executed checks; `validate_issues.py` MUST NOT reinterpret manifest payload semantics. | keep shared contract and deterministic round-trip tests synchronized when manifest schema evolves | ☑ |
 | Triage routing | `scripts/triage_router.py`, `docs/qa/triage-routing.yaml` | inventory complete | unknown pending router-consumer contract audit | possible (risk of reinterpreting upstream gate semantics) | TBD | verify router consumes stabilized outputs without semantic reinterpretation; align routing config docs/tests | ☐ |
-| Integration proof | relevant tests under `tests/` | inventory complete | unknown (deterministic multi-surface proof not yet selected) | N/A | TBD | select one deterministic boundary test (gate -> validators or issue -> manifest linkage) and define expected assertions | ☐ |
+| Integration proof | relevant tests under `tests/` | reconciled | yes (deterministic policy-split proof now asserts diff-oriented readiness checks propagate fallback refs while commit-traceability fails closed unless explicitly opted into degraded mode) | N/A | **Canonical decision (implemented):** keep integration proof at the policy boundary where fallback refs are acceptable for diff-oriented checks but non-authoritative for commit-traceability by default. | preserve the policy-split proof as base-ref resolution and validator boundaries evolve | ☑ |
 
 ## Duplicate / superseded path audit
 
@@ -94,6 +94,11 @@ sed -n '180,430p' tests/test_validate_issue_links.py
 sed -n '450,520p' tests/test_all_green_gate.py
 sed -n '100,170p' tests/test_validate_issues.py
 rg -n "artifacts/verification|run_id|Verification manifest|Run ID|checks" scripts/validate_issues.py
+
+# pass-six issue status/state reconciliation (docs vs validator + transitions)
+rg -n "Status/state enforcement matrix|triage_intake|governed_execution" docs/issues.md scripts/validate_issues.py tests/test_validate_issues.py
+python -m pytest tests/test_validate_issues.py
+python scripts/all_green_gate.py
 rg -n "read_text|json.loads|artifacts/verification|run_id|checks" scripts/all_green_gate.py
 rg -n "^def " scripts/all_green_gate.py scripts/validate_issue_links.py scripts/validate_issues.py scripts/governance_rules.py
 rg -n "^from scripts|^import scripts|governance_rules" scripts/all_green_gate.py scripts/validate_issue_links.py scripts/validate_issues.py
@@ -126,6 +131,8 @@ rg -n "write_verification_manifest|validate_verification_manifest_reference|veri
 - Pass four shared-helper inspection confirmed duplicate production implementations of `git_ref_exists` and `resolve_base_ref` across `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py`. `git_ref_exists` is functionally identical; `resolve_base_ref` shares the same control flow and fallback order, with only caller-facing degraded-mode note wording differing. Current tests validate per-script helper copies rather than a single shared helper path.
 - Pass five recorded implementation reconciliation on `main`: changed-path skip-policy behavior is now implemented (governed-surface matrix + full-check override) and covered by deterministic `tests/test_all_green_gate.py` coverage; checklist wording now reflects reconciled status.
 - Pass five also confirmed manifest round-trip proof is already present on `main` via existing tests, so the remaining manifest gap is closed; action shifts to preserving current contract coverage as schema/validator expectations evolve.
+- Pass six reconciled issue status/state semantics by declaring docs canonical and aligning validator enforcement + deterministic transition tests, then marked this checklist surface verified.
+- Follow-up tightening pass recorded commit-traceability fallback semantics explicitly: `validate_issue_links.py` now fails closed when requested base refs degrade to fallback mode unless `--allow-degraded-commit-traceability` is explicitly provided.
 
 ## Freeze-exit recommendation
 
diff --git a/docs/issues/evidence/work-history-assessment-2026-03-17.md b/docs/issues/evidence/work-history-assessment-2026-03-17.md
index 25c22f3..e7ee035 100644
--- a/docs/issues/evidence/work-history-assessment-2026-03-17.md
+++ b/docs/issues/evidence/work-history-assessment-2026-03-17.md
@@ -15,6 +15,8 @@ Parent context: stabilization effort after governance drift in PRs #481–#489.
   - Follow-on PRs reviewed completion criteria and synchronized checklist claims against implementation status.
 - **#506–#510 (2026-03-17): targeted corrective slices.**
   - Shared governance rule primitives/test shape, strict triage cross-validator matrix coverage, feature-status linkage normalization, and explicit verification-manifest contract semantics were landed in narrower slices.
+- **post-#510 follow-up (2026-03-17): commit-traceability fallback semantics tightened.**
+  - `validate_issue_links.py` now treats commit-history ISSUE-link checks as fail-closed when the requested base ref degrades to fallback mode, with explicit opt-in for degraded container checks.
 
 ## Code-quality and governance-quality evaluation
 
@@ -26,12 +28,8 @@ Parent context: stabilization effort after governance drift in PRs #481–#489.
 
 ### Remaining concerns
 
-- **Shared helper centralization and policy separation are not complete in production code paths.**
-  - `git_ref_exists` and `resolve_base_ref` are still duplicated in `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py`.
-  - The checklist correctly keeps this surface at `decision made`, not reconciled.
-  - The remaining issue is not only duplicate code removal: caller-specific safety requirements for degraded base-ref fallback are not yet explicitly separated. The `HEAD~1` incident showed that fallback semantics acceptable for diff-oriented checks may be unsafe for commit-traceability validation.
 - **Several ownership-boundary surfaces remain inventory-level.**
-  - Issue schema/state, issue-link validator boundary, RED_TAG derivation audit, gate-profile consistency, feature linkage fallback precedence, triage routing consumer contract, and deterministic integration proof selection are not closed.
+  - Issue schema/state, issue-link validator boundary, RED_TAG derivation audit, gate-profile consistency, feature linkage fallback precedence, and triage routing consumer contract are not closed.
 - **Freeze exit is still not ready.**
   - Checklist status remains active temporary freeze and not-ready-to-lift.
 
@@ -43,12 +41,12 @@ Parent context: stabilization effort after governance drift in PRs #481–#489.
 
 - The storyline is still best described as **diagnosis -> freeze -> partial reconciliation -> open enforcement/exit**.
 - The prior assessment is correct that **manifest semantics** and **changed-path skip policy** are the two strongest closed/reconciled surfaces.
-- The prior assessment is correct that broader governance ownership/enforcement closure is still incomplete.
+- The prior assessment is correct that broader governance ownership/enforcement closure is still incomplete, even after the commit-traceability fallback tightening landed.
 
 ### Adjustments recommended
 
-1. **Treat #497 carefully in narrative wording.**
-   - Even though PR #497 title suggests centralization progress, current checklist state and code inspection still show duplicated helper implementations; do not present this surface as reconciled yet.
+1. **Treat pre-reconciliation history carefully in narrative wording.**
+   - Older references to helper duplication are now historical context after shared primitive centralization and explicit consumer-policy wrapper naming landed.
 2. **Keep “freeze exit not ready” explicit.**
    - The checklist still requires all rows to be verified or explicitly deferred before recommending freeze lift.
 3. **Prefer “stabilizing” wording over “stabilized.”**
@@ -57,4 +55,4 @@ Parent context: stabilization effort after governance drift in PRs #481–#489.
 ## Recommended concise status line
 
 **Current repo perspective (2026-03-17):**
-Manifest contract semantics are **verified**, changed-path skip policy is **reconciled**, and corrective sequencing quality improved; however, shared-helper centralization and caller-specific fallback-policy separation remain incomplete, several validator ownership surfaces remain at **inventory complete**, and freeze exit is still not ready.
+Manifest contract semantics are **verified**, changed-path skip policy is **reconciled**, and commit-traceability fallback semantics are now explicitly tightened for the issue-link validator with deterministic policy-split proof coverage; several validator ownership surfaces still remain at **inventory complete**, and freeze exit is still not ready.
diff --git a/scripts/all_green_gate.py b/scripts/all_green_gate.py
index 7098add..243938e 100755
--- a/scripts/all_green_gate.py
+++ b/scripts/all_green_gate.py
@@ -206,12 +206,17 @@ def extract_kpi_reason_classification(stdout: str) -> str | None:
     return reason if isinstance(reason, str) else None
 
 
-def git_ref_exists(ref: str) -> bool:
-    return governance_git_ref_exists(ref, repo_root=REPO_ROOT)
+def resolve_best_effort_diff_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
+    """Resolve base refs for diff-oriented checks that can run on fallback history."""
+    return governance_resolve_base_ref(
+        base_ref,
+        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),
+    )
 
 
 def resolve_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
-    return governance_resolve_base_ref(base_ref, ref_exists=git_ref_exists)
+    """Backward-compatible alias for diff-oriented base-ref resolution."""
+    return resolve_best_effort_diff_base_ref(base_ref)
 
 
 def default_profile_for_environment() -> str:
@@ -711,7 +716,7 @@ def main() -> int:
         print(f"[INFO] Verification manifest written: {manifest_path.relative_to(REPO_ROOT)}")
         return 1
 
-    effective_base_ref, base_ref_notes = resolve_base_ref(args.base_ref)
+    effective_base_ref, base_ref_notes = resolve_best_effort_diff_base_ref(args.base_ref)
     for note in base_ref_notes:
         print(f"[WARN] {note}")
     if args.base_ref == "origin/main" and effective_base_ref in {"HEAD~1", "HEAD"}:
diff --git a/scripts/governance_rules.py b/scripts/governance_rules.py
index 3fc8780..f8c3a00 100644
--- a/scripts/governance_rules.py
+++ b/scripts/governance_rules.py
@@ -18,6 +18,7 @@ ORIGIN_MAIN_FALLBACK_NOTE: Final[str] = (
     "Base ref 'origin/main' is unavailable; falling back to '{fallback}'.\n"
     "       This is expected in Codex task containers or shallow CI clones.\n"
     "       Governance diff checks are running against a reduced baseline.\n"
+    "       Commit-traceability checks may still fail closed unless degraded mode is explicitly allowed.\n"
     "       For authoritative results, run locally with 'git fetch origin main' first. "
     "(Unless you are ChatGPT/Codex!)"
 )
diff --git a/scripts/validate_issue_links.py b/scripts/validate_issue_links.py
index fafd695..9c845c4 100644
--- a/scripts/validate_issue_links.py
+++ b/scripts/validate_issue_links.py
@@ -125,12 +125,17 @@ def run_git(args: list[str]) -> str:
     return result.stdout
 
 
-def git_ref_exists(ref: str) -> bool:
-    return governance_git_ref_exists(ref, repo_root=REPO_ROOT)
+def resolve_exact_commit_traceability_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
+    """Resolve base refs for commit-traceability checks that fail closed on degradation."""
+    return governance_resolve_base_ref(
+        base_ref,
+        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),
+    )
 
 
 def resolve_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
-    return governance_resolve_base_ref(base_ref, ref_exists=git_ref_exists)
+    """Backward-compatible alias for commit-traceability base-ref resolution."""
+    return resolve_exact_commit_traceability_base_ref(base_ref)
 
 
 def load_canonical_sections() -> list[str]:
@@ -458,7 +463,7 @@ def validate_red_tag_generated_content(failures: list[ValidationFailure]) -> Non
 def main() -> int:
     args = parse_args()
     failures: list[ValidationFailure] = []
-    effective_base_ref, resolution_notes = resolve_base_ref(args.base_ref)
+    effective_base_ref, resolution_notes = resolve_exact_commit_traceability_base_ref(args.base_ref)
     for note in resolution_notes:
         print(f"[WARN] {note}")
 
diff --git a/scripts/validate_issues.py b/scripts/validate_issues.py
index 602e3d1..9aeae1e 100755
--- a/scripts/validate_issues.py
+++ b/scripts/validate_issues.py
@@ -36,6 +36,24 @@ TRIAGE_INTAKE_SECTIONS = ["ID", "Title", "Problem", "Owner", "Severity", "Next A
 ISSUE_STATE_TRIAGE_INTAKE = "triage_intake"
 ISSUE_STATE_GOVERNED_EXECUTION = "governed_execution"
 
+ALLOWED_ISSUE_STATES = {
+    ISSUE_STATE_TRIAGE_INTAKE,
+    ISSUE_STATE_GOVERNED_EXECUTION,
+}
+
+ALLOWED_STATUS_VALUES = {
+    "open",
+    "in_progress",
+    "blocked",
+    "resolved",
+    "closed",
+}
+
+ALLOWED_STATE_STATUS_TRANSITIONS = {
+    ISSUE_STATE_TRIAGE_INTAKE: {"open"},
+    ISSUE_STATE_GOVERNED_EXECUTION: ALLOWED_STATUS_VALUES,
+}
+
 
 def parse_args() -> argparse.Namespace:
     parser = argparse.ArgumentParser(description=__doc__)
@@ -72,12 +90,17 @@ def load_canonical_sections() -> list[str]:
     return parse_canonical_sections(text)
 
 
-def git_ref_exists(ref: str) -> bool:
-    return governance_git_ref_exists(ref, repo_root=REPO_ROOT)
+def resolve_safe_changed_path_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
+    """Resolve base refs for changed-path discovery with safe full-check fallback."""
+    return governance_resolve_base_ref(
+        base_ref,
+        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),
+    )
 
 
 def resolve_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
-    return governance_resolve_base_ref(base_ref, ref_exists=git_ref_exists)
+    """Backward-compatible alias for changed-path base-ref resolution."""
+    return resolve_safe_changed_path_base_ref(base_ref)
 
 
 def run_git_diff_for_added_files(base_ref: str) -> list[Path]:
@@ -137,15 +160,18 @@ def validate_issue_files(issue_files: list[Path], canonical_sections: list[str],
         issue_state = field_value(text, "Issue State").lower()
         status = field_value(text, "Status").lower()
 
+        if issue_state and issue_state not in ALLOWED_ISSUE_STATES:
+            allowed = ", ".join(sorted(ALLOWED_ISSUE_STATES))
+            failures.append(f"{rel}: invalid Issue State '{issue_state}'. Allowed values: {allowed}.")
+
+        if status and status not in ALLOWED_STATUS_VALUES:
+            allowed = ", ".join(sorted(ALLOWED_STATUS_VALUES))
+            failures.append(f"{rel}: invalid Status '{status}'. Allowed values: {allowed}.")
+
         if issue_state == ISSUE_STATE_TRIAGE_INTAKE:
             missing = missing_canonical_sections(text, TRIAGE_INTAKE_SECTIONS)
             if missing:
                 failures.append(f"{rel}: triage_intake missing required fields: {', '.join(missing)}")
-
-            if status and status != "open":
-                failures.append(
-                    f"{rel}: triage_intake issues must remain Status 'open' and be promoted to governed_execution before '{status}'."
-                )
             if not status:
                 failures.append(
                     f"{rel}: triage_intake issues must declare Status 'open' to enforce promotion SLA before in_progress."
@@ -156,6 +182,15 @@ def validate_issue_files(issue_files: list[Path], canonical_sections: list[str],
             if missing:
                 failures.append(f"{rel}: missing canonical sections: {', '.join(missing)}")
 
+        if issue_state in ALLOWED_STATE_STATUS_TRANSITIONS and status in ALLOWED_STATUS_VALUES:
+            allowed_state_statuses = ALLOWED_STATE_STATUS_TRANSITIONS[issue_state]
+            if status not in allowed_state_statuses:
+                allowed = ", ".join(sorted(allowed_state_statuses))
+                failures.append(
+                    f"{rel}: invalid state/status transition Issue State '{issue_state}' with Status '{status}'. "
+                    f"Allowed statuses for this state: {allowed}."
+                )
+
         if ruleset == RULESET_TRIAGE:
             continue
 
@@ -175,7 +210,7 @@ def main() -> int:
 
     validate_pr_body(args.pr_body_file, failures)
 
-    effective_base_ref, resolution_notes = resolve_base_ref(args.base_ref)
+    effective_base_ref, resolution_notes = resolve_safe_changed_path_base_ref(args.base_ref)
     for note in resolution_notes:
         print(f"[WARN] {note}")
 
diff --git a/tests/test_all_green_gate.py b/tests/test_all_green_gate.py
index 70b7419..0b7a028 100644
--- a/tests/test_all_green_gate.py
+++ b/tests/test_all_green_gate.py
@@ -116,9 +116,9 @@ def test_main_writes_behave_remediation_to_json_summary(
 
 
 def test_resolve_base_ref_falls_back_when_origin_main_missing(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setattr(all_green_gate, "git_ref_exists", lambda ref: ref == "HEAD~1")
+    monkeypatch.setattr(all_green_gate, "governance_git_ref_exists", lambda ref, *, repo_root: ref == "HEAD~1")
 
-    resolved, notes = all_green_gate.resolve_base_ref("origin/main")
+    resolved, notes = all_green_gate.resolve_best_effort_diff_base_ref("origin/main")
 
     assert resolved == "HEAD~1"
     assert any("falling back to 'HEAD~1'" in note for note in notes)
@@ -128,9 +128,9 @@ def test_resolve_base_ref_falls_back_when_origin_main_missing(monkeypatch: pytes
 
 
 def test_resolve_base_ref_returns_canonical_note_when_no_refs_available(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setattr(all_green_gate, "git_ref_exists", lambda _ref: False)
+    monkeypatch.setattr(all_green_gate, "governance_git_ref_exists", lambda _ref, *, repo_root: False)
 
-    resolved, notes = all_green_gate.resolve_base_ref("origin/main")
+    resolved, notes = all_green_gate.resolve_best_effort_diff_base_ref("origin/main")
 
     assert resolved is None
     assert notes == [
@@ -160,7 +160,7 @@ def test_main_propagates_effective_base_ref_to_governance_checks_in_readiness_pr
         ),
     )
     monkeypatch.setattr(all_green_gate.importlib.util, "find_spec", lambda _name: object())
-    monkeypatch.setattr(all_green_gate, "resolve_base_ref", lambda _ref: ("HEAD~1", []))
+    monkeypatch.setattr(all_green_gate, "resolve_best_effort_diff_base_ref", lambda _ref: ("HEAD~1", []))
 
     captured_checks: list[all_green_gate.GateCheck] = []
 
diff --git a/tests/test_base_ref_policy_split.py b/tests/test_base_ref_policy_split.py
new file mode 100644
index 0000000..775a6d8
--- /dev/null
+++ b/tests/test_base_ref_policy_split.py
@@ -0,0 +1,40 @@
+from __future__ import annotations
+
+import importlib.util
+import sys
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
+
+
+def _load_module(module_name: str, path: Path):
+    spec = importlib.util.spec_from_file_location(module_name, path)
+    assert spec and spec.loader
+    module = importlib.util.module_from_spec(spec)
+    sys.modules[spec.name] = module
+    spec.loader.exec_module(module)
+    return module
+
+
+all_green_gate = _load_module("all_green_gate", _SCRIPTS_DIR / "all_green_gate.py")
+validate_issue_links = _load_module("validate_issue_links", _SCRIPTS_DIR / "validate_issue_links.py")
+
+
+def test_base_ref_policy_split_between_diff_checks_and_commit_traceability() -> None:
+    """Diff-oriented checks accept fallback refs while commit traceability fails closed."""
+    readiness_checks = all_green_gate.build_checks(base_ref="HEAD~1", profile="readiness")
+    issue_link_check = next(check for check in readiness_checks if check.name == "qa_validate_issue_links")
+
+    assert issue_link_check.command[-1] == "HEAD~1"
+
+    failures: list[validate_issue_links.ValidationFailure] = []
+    allowed = validate_issue_links.commit_traceability_requires_exact_base_ref(
+        requested_base_ref="origin/main",
+        effective_base_ref="HEAD~1",
+        allow_degraded_commit_traceability=False,
+        failures=failures,
+    )
+
+    assert allowed is False
+    assert failures
+    assert "fail closed" in failures[0].message
diff --git a/tests/test_validate_issue_links.py b/tests/test_validate_issue_links.py
index fd2e7d0..84ed1fb 100644
--- a/tests/test_validate_issue_links.py
+++ b/tests/test_validate_issue_links.py
@@ -163,9 +163,9 @@ def test_validate_red_tag_generated_content_accepts_match(
 
 
 def test_resolve_base_ref_uses_canonical_missing_requested_note(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setattr(validate_issue_links, "git_ref_exists", lambda _ref: False)
+    monkeypatch.setattr(validate_issue_links, "governance_git_ref_exists", lambda _ref, *, repo_root: False)
 
-    resolved, notes = validate_issue_links.resolve_base_ref("feature/base")
+    resolved, notes = validate_issue_links.resolve_exact_commit_traceability_base_ref("feature/base")
 
     assert resolved is None
     assert notes == [
@@ -525,3 +525,19 @@ def test_commit_traceability_can_opt_in_to_degraded_mode() -> None:
 
     assert allowed is True
     assert failures == []
+
+
+def test_commit_traceability_failure_message_mentions_requested_and_effective_refs() -> None:
+    failures: list[validate_issue_links.ValidationFailure] = []
+
+    allowed = validate_issue_links.commit_traceability_requires_exact_base_ref(
+        "origin/main",
+        "HEAD~1",
+        allow_degraded_commit_traceability=False,
+        failures=failures,
+    )
+
+    assert allowed is False
+    assert failures
+    assert "Requested 'origin/main' but resolved 'HEAD~1'" in failures[0].hint
+    assert "--allow-degraded-commit-traceability" in failures[0].hint
diff --git a/tests/test_validate_issues.py b/tests/test_validate_issues.py
index 920da81..31a27a2 100644
--- a/tests/test_validate_issues.py
+++ b/tests/test_validate_issues.py
@@ -9,6 +9,26 @@ import pytest
 _SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
 
 
+CANONICAL_GOVERNED_SECTIONS = [
+    "ID",
+    "Title",
+    "Status",
+    "Issue State",
+    "Severity",
+    "Owner",
+    "Created",
+    "Target Sprint",
+    "Principle Alignment",
+    "Problem Statement",
+    "Evidence",
+    "Impact",
+    "Acceptance Criteria",
+    "Work Plan",
+    "Verification",
+    "Closure Notes",
+]
+
+
 def _load_module(module_name: str, path: Path):
     spec = importlib.util.spec_from_file_location(module_name, path)
     assert spec and spec.loader
@@ -22,9 +42,9 @@ validate_issues = _load_module("validate_issues", _SCRIPTS_DIR / "validate_issue
 
 
 def test_resolve_base_ref_uses_canonical_missing_origin_note(monkeypatch: pytest.MonkeyPatch) -> None:
-    monkeypatch.setattr(validate_issues, "git_ref_exists", lambda _ref: False)
+    monkeypatch.setattr(validate_issues, "governance_git_ref_exists", lambda _ref, *, repo_root: False)
 
-    resolved, notes = validate_issues.resolve_base_ref("origin/main")
+    resolved, notes = validate_issues.resolve_safe_changed_path_base_ref("origin/main")
 
     assert resolved is None
     assert notes == [
@@ -38,6 +58,27 @@ def _write_issue(tmp_path: Path, name: str, content: str) -> Path:
     return path
 
 
+def _governed_issue_content(status: str) -> str:
+    return f"""
+**ID:** ISSUE-9999
+**Title:** Full issue
+**Status:** {status}
+**Issue State:** governed_execution
+**Severity:** green
+**Owner:** Team
+**Created:** 2026-01-01
+**Target Sprint:** S1
+**Principle Alignment:** deterministic
+**Problem Statement:** Defined problem
+**Evidence:** Logs
+**Impact:** Delivery
+**Acceptance Criteria:** Tests pass
+**Work Plan:** Implement
+**Verification:** Run pytest
+**Closure Notes:** Pending
+"""
+
+
 def test_validate_issue_files_accepts_triage_intake_minimal_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
     issue = _write_issue(
         tmp_path,
@@ -62,65 +103,32 @@ def test_validate_issue_files_accepts_triage_intake_minimal_schema(tmp_path: Pat
     assert failures == []
 
 
-def test_validate_issue_files_accepts_governed_execution_full_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
-    issue = _write_issue(
-        tmp_path,
-        "ISSUE-9999-governed.md",
-        """
-**ID:** ISSUE-9999
-**Title:** Full issue
-**Status:** in_progress
-**Issue State:** governed_execution
-**Severity:** green
-**Owner:** Team
-**Created:** 2026-01-01
-**Target Sprint:** S1
-**Principle Alignment:** deterministic
-**Problem Statement:** Defined problem
-**Evidence:** Logs
-**Impact:** Delivery
-**Acceptance Criteria:** Tests pass
-**Work Plan:** Implement
-**Verification:** Run pytest
-**Closure Notes:** Pending
-""",
-    )
+@pytest.mark.parametrize("status", ["open", "in_progress", "blocked", "resolved", "closed"])
+def test_validate_issue_files_allows_governed_execution_status_transitions(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
+) -> None:
+    issue = _write_issue(tmp_path, f"ISSUE-9999-governed-{status}.md", _governed_issue_content(status))
 
     monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)
 
     failures: list[str] = []
-    canonical = [
-        "ID",
-        "Title",
-        "Status",
-        "Issue State",
-        "Severity",
-        "Owner",
-        "Created",
-        "Target Sprint",
-        "Principle Alignment",
-        "Problem Statement",
-        "Evidence",
-        "Impact",
-        "Acceptance Criteria",
-        "Work Plan",
-        "Verification",
-        "Closure Notes",
-    ]
-    validate_issues.validate_issue_files([issue], canonical, failures, ruleset=validate_issues.RULESET_STRICT)
+    validate_issues.validate_issue_files([issue], CANONICAL_GOVERNED_SECTIONS, failures, ruleset=validate_issues.RULESET_STRICT)
 
     assert failures == []
 
 
-def test_validate_issue_files_rejects_triage_intake_in_progress_transition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+@pytest.mark.parametrize("status", ["in_progress", "blocked", "resolved", "closed"])
+def test_validate_issue_files_rejects_triage_intake_disallowed_statuses(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
+) -> None:
     issue = _write_issue(
         tmp_path,
-        "ISSUE-7777-invalid-transition.md",
-        """
+        f"ISSUE-7777-invalid-{status}.md",
+        f"""
 **ID:** ISSUE-7777
 **Title:** Invalid transition
 **Issue State:** triage_intake
-**Status:** in_progress
+**Status:** {status}
 **Problem:** Initial report
 **Owner:** Team
 **Severity:** green
@@ -133,7 +141,40 @@ def test_validate_issue_files_rejects_triage_intake_in_progress_transition(tmp_p
     failures: list[str] = []
     validate_issues.validate_issue_files([issue], ["ID", "Title", "Status", "Issue State"], failures, ruleset=validate_issues.RULESET_STRICT)
 
-    assert any("triage_intake issues must remain Status 'open'" in failure for failure in failures)
+    assert any("invalid state/status transition" in failure for failure in failures)
+
+
+def test_validate_issue_files_rejects_invalid_status_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+    issue = _write_issue(tmp_path, "ISSUE-7000-invalid-status.md", _governed_issue_content("paused"))
+
+    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)
+
+    failures: list[str] = []
+    validate_issues.validate_issue_files([issue], CANONICAL_GOVERNED_SECTIONS, failures, ruleset=validate_issues.RULESET_STRICT)
+
+    assert any("invalid Status 'paused'" in failure for failure in failures)
+
+
+def test_validate_issue_files_rejects_invalid_issue_state_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+    issue = _write_issue(
+        tmp_path,
+        "ISSUE-7001-invalid-state.md",
+        """
+**ID:** ISSUE-7001
+**Title:** Invalid issue state
+**Issue State:** archived
+**Status:** open
+**Severity:** amber
+**Owner:** Team
+""",
+    )
+
+    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)
+
+    failures: list[str] = []
+    validate_issues.validate_issue_files([issue], ["ID", "Title", "Issue State", "Status", "Severity", "Owner"], failures, ruleset=validate_issues.RULESET_STRICT)
+
+    assert any("invalid Issue State 'archived'" in failure for failure in failures)
 
 
 def test_validate_pr_body_uses_shared_metadata_issue_reference_primitive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
