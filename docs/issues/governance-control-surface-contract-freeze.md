# Governance control-surface canonical contract (temporary freeze)

> Status: **Temporary freeze active**
>
> Effective: 2026-03-16 (until explicitly lifted in a follow-up issue/PR)
>
> Scope: Canonical source of truth for governance control surfaces implicated by contract drift.

## Purpose

This document is the single source of truth for intended behavior during the governance stabilization window described in `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`.

During the freeze, contributors MUST treat the contract below as normative and MUST avoid opportunistic behavior edits outside an explicitly scoped contract-reconciliation change.

## Precedence during freeze

If this document conflicts with `docs/issues.md`, script help text, test fixtures, YAML/config files, example artifacts, or prior PR descriptions/comments, **this document takes precedence** until the freeze is explicitly lifted.

Any discrepancy discovered during freeze MUST be treated as stabilization work: align code, docs, tests, and fixtures to this contract rather than inferring intended behavior from older or parallel sources.

## Freeze directive

Until freeze lift, do **not** submit opportunistic changes to these surfaces:

- `scripts/all_green_gate.py`
- `scripts/validate_issue_links.py`
- `scripts/validate_issues.py`
- `scripts/governance_rules.py`
- `docs/issues.md`
- RED_TAG generation/indexing behavior
- verification manifest semantics
- triage routing behavior
- `tests/test_all_green_gate.py`
- `tests/test_validate_issue_links.py`
- `tests/test_validate_issues.py`
- `docs/qa/feature-status.yaml`
- `docs/qa/triage-routing.yaml`
- example verification manifests, fixture issue files, and other artifacts that encode governance semantics

Allowed changes during freeze:

- bug fixes that restore behavior to this frozen contract,
- deterministic test updates that align with this contract,
- documentation clarifications that do not alter semantics.

For avoidance of doubt, an allowed **bug fix** during freeze:

- restores behavior already stated in this document,
- does **not** introduce a new rule, state, derivation path, skip trigger, manifest meaning, or routing interpretation,
- does **not** expand acceptance criteria beyond what is frozen here,
- does **not** rely on old PR text or legacy implementation as the authority when this document is more specific.

Any semantic change proposal MUST include:

1. explicit before/after contract delta,
2. dependency order against coupled surfaces,
3. synchronized updates across code + docs + tests.

## Required stabilization audit during freeze

During the freeze window, stabilization work MUST explicitly check for duplicate, superseded, shadowed, or partially overlapping implementations introduced across PRs `#481`–`#489`.

For each affected control surface, the repo must converge on:

- one canonical implementation path,
- one canonical documentation path,
- one canonical test expectation set.

## Frozen intended behavior by control surface

### 1) Validator rulesets (`scripts/governance_rules.py`, issue validators)

- Governance rule primitives are centralized and reused; validators must not fork equivalent logic in ad-hoc form.
- `scripts/validate_issue_links.py` validates issue-link integrity, including verification manifest references when present.
- `scripts/validate_issues.py` validates canonical issue schema/state integrity and policy conformance.
- Base-ref resolution policy is canonicalized in `scripts/governance_rules.py`: prefer requested `origin/main`; when unavailable, optionally recover into `refs/codex/origin-main` (requires `ALLOW_REMOTE_BASE_REF_RECOVERY=true` and `GIT_ORIGIN_URL`), then fall back to `HEAD~1` -> `HEAD` with explicit warnings.
- `scripts/validate_issue_links.py` commit-traceability checks may accept recovered `refs/codex/origin-main`, but must continue to fail closed for degraded `HEAD~1`/`HEAD` unless degraded mode is explicitly allowed.

### 2) Issue states (canonical model)

The authoritative issue-state model remains:

- `Issue State: triage_intake` allowed only with `Status: open`.
- Transition to `Status: in_progress` requires promotion to `Issue State: governed_execution`.
- Governed execution status values remain exactly: `open`, `in_progress`, `blocked`, `resolved`, `closed`.

### 3) RED_TAG derivation

- Source of truth is issue metadata in `docs/issues/ISSUE-*.md`.
- `docs/issues/RED_TAG.md` is generated output, not hand-edited policy content.
- Red-tag eligibility remains severity-driven (`Severity: red`) with workflow obligations defined in `docs/issues.md`.

### 4) Gate profiles (`scripts/all_green_gate.py`)

- The gate profile layer (triage/readiness semantics) is canonical and must continue to run through shared governance checks rather than bespoke profile-local checks.
- Local/default developer execution remains `triage`; CI/release semantics remain `readiness` unless and until a reviewed contract revision changes that rule.
- Profile behavior changes require synchronized updates to gate documentation and downstream consumers.
- Skipped checks must remain visible in console/JSON output with explicit skip reasons.

### 5) Changed-path skip policy

- Changed-path-aware skipping remains deterministic and policy-bound.
- Skip logic must never mask required governance checks for files that fall inside the governed control surfaces.
- Any skip-rule adjustment must include explicit proof that required checks cannot be silently bypassed.
- **If any frozen control-surface file or governed semantic fixture/config changes, path-based skip reduction is disabled and full governance checks must run for that invocation.**

### 6) Verification manifest semantics

- Verification manifests referenced from issue files must resolve to existing files and include canonical all-green gate checks.
- Run ID linkage between issue record and manifest remains required where manifest references are used.
- Manifest schema/meaning changes require synchronized validator and documentation updates.
- Manifest references remain optional unless another canonical policy document is updated to require them.
- A referenced manifest that is missing, malformed, or inconsistent with required linkage is a validation failure, not an advisory warning.

### 7) Triage routing

- Triage routing consumes stabilized gate outputs and issue/RED_TAG signals; routing must not reinterpret upstream semantics implicitly.
- Routing changes are blocked during freeze unless they strictly restore consistency with this canonical contract.

## Contract authority

During freeze, contract interpretation disputes must be resolved by the designated stabilization owner for governance control surfaces. Changes that cannot name that owner/reviewer in the associated issue or PR are not ready for merge.

## Change-control protocol while freeze is active

1. Open/attach an issue with explicit governance-contract scope.
2. Document contract delta first (this file + any impacted policy docs).
3. Update implementation and deterministic tests in the same change set.
4. Run canonical gate: `python scripts/all_green_gate.py`.
5. Include dependency ordering notes when multiple control surfaces are touched.
6. For any change touching multiple frozen control surfaces, include or update at least one deterministic end-to-end integration test covering the affected interaction boundary.

## Exit criteria for lifting freeze

Freeze may be lifted only when all are true:

- a reviewed canonical contract revision is merged,
- validators/gate/tests align with the revised contract,
- no unresolved drift remains across rulesets, issue states, RED_TAG derivation, gate profiles, skip policy, manifest semantics, and triage routing.

