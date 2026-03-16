# Governance control-surface completion audit (2026-03-16)

This audit answers the full completion checklist for the governance-control-surface PR series using current repository code, docs, and deterministic tests.

## Overall status snapshot

- **Mode:** stabilization mode (not verified-complete).
- **Canonical freeze:** active and normative.
- **Scope posture:** intentionally bounded stabilization scope, with several control surfaces still open for reconciliation.

Primary evidence anchors:

- `docs/issues/governance-control-surface-contract-freeze.md`
- `docs/issues/evidence/governance-stabilization-checklist.md`
- `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`

---

## 1) Scope and completion

- Capability surfaces have landed for shared governance primitives, rulesets, issue-state model enforcement, RED_TAG generation+parity, gate profiles, changed-path skip policy, manifest validation, and triage routing.
- These are discoverable in code/docs/tests, and the stabilization status note frames this as intentionally bounded (no net-new governance automation during freeze), but checklist rows still mark multiple surfaces as open/partial, so the series is not yet closed as verified-complete.

Status: **Partially landed / still stabilizing**.

---

## 2) Canonical contract and freeze

- One canonical freeze document exists and is explicitly declared as temporary normative precedence.
- It distinguishes frozen canonical behavior and describes what changes are/are not allowed during freeze.
- It names behavior families that are frozen and defines explicit freeze-lift/exit conditions.
- Current docs indicate stabilization is in progress and not yet complete.

Status: **Contract exists and is active; exit not yet reached**.

---

## 3) Shared governance rules and validator boundaries

- `scripts/governance_rules.py` is now the shared home for key primitives (issue refs, section parsing, base-ref resolution).
- Both validators import shared primitives.
- Boundary intent is documented (issues validator = schema/state; links validator = linkage/reference/metadata), but **duplication still exists** (canonical section presence checks + PR reference checks).
- Shared-behavior parity tests exist for some shared helpers.

Status: **Improved, but not fully cleanly separated**.

---

## 4) CLI and ruleset behavior

- Both validators expose `--ruleset {strict,triage}` with strict default.
- Documentation describes strict vs triage at a high level.
- Ruleset coverage is currently stronger for `validate_issues.py` than for `validate_issue_links.py`; there is not yet a full explicit strict-vs-triage assertion matrix for both validators.

Status: **CLI landed; coverage incomplete for full ruleset matrix**.

---

## 5) Issue schema and state model

- Two-state model is documented in `docs/issues.md` (`triage_intake`, `governed_execution`).
- Promotion-before-`in_progress` is documented and enforced in `validate_issues.py`.
- `triage_intake` minimal schema acceptance and invalid transition rejection are covered by tests.
- Current repository issue inventory/validation passes with no detected state violations.

Status: **Implemented and currently clean for existing issue files**.

---

## 6) RED_TAG derivation

- RED_TAG is documented and rendered as generated output.
- `generate_red_tag_index.py` is canonical generator.
- `validate_issue_links.py` checks committed RED_TAG content against generated output.
- Existing RED_TAG content is currently in sync with generator output.

Status: **Implemented and deterministic in current state**.

---

## 7) Gate profile model

- `all_green_gate.py` has explicit `triage`/`readiness` profiles.
- Default profile is triage locally and readiness in CI/release envs.
- Profile composition is explicit in code and reflected in testing docs.
- JSON summary separates `product_failures` from `governance_failures`.
- Tests cover profile defaults and check composition.

Status: **Implemented and documented**.

---

## 8) Changed-path-aware governance skipping

- Skip policy exists and includes freeze-governed override paths.
- `--force-full-governance` fully overrides skip behavior.
- Skip reasons are surfaced in console and JSON summary.
- Test coverage exists for key skip and override behaviors.
- Contract is still under active freeze, so ratified final post-freeze policy is not yet declared.

Status: **Implemented; still governed by active stabilization freeze**.

---

## 9) Feature-status and issue linkage

- `feature-status.yaml` supports explicit `issue_ids`, but compatibility fields (`open_issues`) and keyword fallback remain present.
- `report_feature_status.py` prefers explicit IDs, supports fallback alias, and warns on keyword-only linkage.
- Tests cover explicit linkage, keyword fallback warnings, and mixed linkage behavior.
- Repo data is mixed (explicit + legacy/fallback patterns), so outputs are useful but not fully normalized.

Status: **Primary mechanism landed; migration incomplete**.

---

## 10) Evidence manifest semantics

- Gate writes verification manifests deterministically with stable required check names.
- Issues docs allow Verification sections to reference manifests + run IDs.
- `validate_issue_links.py` validates manifest path existence, run-id consistency, JSON shape, and required checks.
- End-to-end producer→consumer round-trip test exists.
- No second competing manifest implementation was found in current code paths.

Status: **Implemented with end-to-end test proof**.

---

## 11) Triage routing

- Router consumes gate summary JSON, but also applies local routing/severity inference logic.
- Docs position routing as optional post-gate step.
- Owner-routing config is externalized in `docs/qa/triage-routing.yaml`.
- Tests exist for route resolution and CLI output.
- Because router adds inference on top of gate failures, semantics are advisory/add-on rather than canonical pass/fail authority.

Status: **Useful add-on; not a canonical gate authority surface**.

---

## 12) Documentation alignment

- README/testing docs align on local triage default and readiness profile usage.
- `docs/issues.md` aligns with two-state issue model and freeze notice.
- `docs/testing-triage.md` aligns with optional triage-router workflow.
- Freeze/status/checklist docs indicate ongoing stabilization and unresolved rows.

Status: **Broadly aligned, but stabilization docs explicitly report unfinished reconciliation work**.

---

## 13) Tests and coherence proof

- There is substantial deterministic unit coverage for major governance components.
- There are targeted cross-surface tests (manifest round-trip, shared-rule parity, skip policy behavior).
- The canonical integrated gate model is documented and executable (`scripts/all_green_gate.py` as authoritative sequence, with explicit triage/readiness profiles), and both profiles currently run green in this workspace (readiness with optional KPI warning semantics). Freeze-exit governance signoff remains a separate stabilization completion step.

Status: **Strong component coverage; final integrated stabilization closure still pending**.

---

## 14) Duplicate intent / supersession risk (#487/#488)

- Repo evidence docs already flag overlap/supersession risk as a stabilization concern.
- Some duplicated validator intent remains (notably schema-section/PR-reference overlap).
- Canonical ownership for every rule is not fully singularized yet.

Status: **Risk reduced, not fully eliminated**.

---

## 15) Repo migration and normalization

- RED_TAG is in-sync and generator-backed.
- Issue files currently pass validators.
- Feature linkage migration toward explicit `issue_ids` is incomplete.
- Evidence/manifest pathways exist and validate; broader historical normalization is still an active stabilization concern.

Status: **Partially complete normalization**.

---

## 16) Governance hardening / recurrence prevention

- Freeze contract requires explicit before/after contract delta + dependency order + synchronized code/docs/tests for semantic changes.
- Mechanical enforcement exists in-repo for at least part of governance hardening: GitHub Actions runs `scripts/validate_issue_links.py` on every pull request.
- Broader hardening dimensions (for example PR dependency declarations, CODEOWNERS-style review constraints, and explicit concurrency prevention rules for coupled governance surfaces) remain partially process-driven and are not fully mechanized from the evidence reviewed in this pass.

Status: **Process guidance present; hard enforcement appears partial**.

---

## 17) Definition-of-done call

- One-sentence ownership can be stated for many surfaces now, but not all are fully de-duplicated.
- Ambiguity remains on some validator boundaries and legacy compatibility pathways.
- Docs/code/tests are much closer, but freeze docs and checklist still report unresolved stabilization items.
- Therefore freeze-exit conditions are **not yet fully met**, and lifting freeze now would risk residual contract drift.

Final status: **Not yet verified-complete; remain in stabilization mode until checklist rows are reconciled and freeze exit criteria are explicitly marked satisfied.**

---

## Evidence commands run for this audit

```bash
python scripts/validate_issues.py --all-issue-files --base-ref HEAD
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD
python scripts/generate_red_tag_index.py --check
python -m pytest tests/test_governance_rules.py tests/test_validate_issues.py tests/test_validate_issue_links.py tests/test_all_green_gate.py tests/test_triage_router.py -q
python scripts/all_green_gate.py
```
