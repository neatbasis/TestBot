# Governance stabilization status note

> Status: Active
>
> Scope: Governance control-surface stabilization after PRs `#481`–`#489`
>
> Canonical references:
>
> - `docs/issues/governance-control-surface-contract-freeze.md`
> - `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
> - `docs/issues/evidence/governance-stabilization-checklist.md`
> - `docs/issues.md`

## Summary

We are in an active stabilization phase for governance control surfaces affected by PRs `#481`–`#489`.

This work began because the PR series evolved one semantically coupled governance subsystem in multiple slices rather than landing a single frozen target contract first. The repo now treats that as a coordination/drift problem requiring temporary contract freeze, explicit audit, canonical-path selection, and staged reconciliation.

The current effort is intentionally bounded. We are not adding new governance automation during this phase. We are freezing the affected contract surfaces, auditing duplicate/superseded behavior, choosing one canonical implementation path per surface, and aligning docs/tests/implementation before lifting the freeze.

## What we have done so far

### 1. Defined the problem and documented the drift pattern

We documented the coordination-failure diagnosis in:

- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`

That document explains why the PR series was vulnerable before code-level review:

- contract written implicitly across merges rather than explicitly once,
- hidden sequencing dependencies across shared control surfaces,
- duplicate-intent risk where similarly scoped changes were queued independently.

It also records the capability-level coupling between:

- shared validator rules,
- issue schema/state model,
- RED_TAG derivation,
- gate profile model,
- changed-path skip policy,
- explicit feature/issue linkage,
- verification manifest semantics,
- triage routing.

### 2. Activated a temporary canonical freeze

We created a temporary freeze document at:

- `docs/issues/governance-control-surface-contract-freeze.md`

During the freeze, that file is the canonical source of truth for:

- validator rulesets,
- issue states,
- RED_TAG derivation,
- gate profiles,
- changed-path skip policy,
- verification manifest semantics,
- triage routing,
- related governed fixtures/config/tests.

The freeze blocks opportunistic semantic edits on these surfaces and requires explicit contract delta, dependency order, and synchronized code/docs/tests updates for any semantic reconciliation change.

### 3. Created a stabilization execution tracker

We created and are maintaining:

- `docs/issues/evidence/governance-stabilization-checklist.md`

This is the main working document for the stabilization effort. It records:

- current status by control surface,
- whether docs/tests agree,
- duplicate/conflict findings,
- canonical decisions,
- required reconciliation work,
- duplicate/superseded path audit findings,
- evidence-gathering command history,
- pass-by-pass notes.

### 4. Completed initial inventory and multiple audit passes

The checklist evidence log shows four stabilization passes so far:

- first-pass inventory,
- changed-path skip-policy analysis,
- manifest/reference ownership and call-path inspection,
- shared-helper duplication inspection.

These passes have converted several earlier suspicions into concrete findings.

## Current focus

The current focus is surface-by-surface stabilization under the active freeze.

### A. Verification manifest semantics

This area now has a ratified analysis decision:

- `scripts/all_green_gate.py` owns verification manifest production only,
- `scripts/validate_issue_links.py` owns manifest reference integrity end-to-end,
- `scripts/validate_issues.py` owns section/schema/state policy only and does not parse manifest payload semantics.

Current remaining risk in this area:

- there is no direct producer→consumer round-trip contract test yet.

### B. Shared governance rules

This area now also has a ratified analysis decision:

- `git_ref_exists` and `resolve_base_ref` are duplicated across:
  - `scripts/all_green_gate.py`
  - `scripts/validate_issue_links.py`
  - `scripts/validate_issues.py`
- `git_ref_exists` is functionally identical,
- `resolve_base_ref` uses the same control flow and fallback order, with only caller-facing degraded-mode note wording differing.

Current retained direction:

- centralize shared base-ref resolution primitives in `scripts/governance_rules.py`,
- keep one shared behavioral implementation,
- allow only thin caller wrappers if caller-specific wording must remain different.

### C. Remaining open stabilization surfaces

The following areas are still open or only partially resolved:

- issue schema/state model,
- issue-link / reference validation authority boundaries,
- RED_TAG derivation,
- gate profiles,
- changed-path skip policy,
- feature-status / issue linkage,
- triage routing,
- final integration proof selection.

## What we plan to do next

### 1. Add a deterministic round-trip manifest contract test

Planned direction:

- generate a manifest via `write_verification_manifest()`,
- reference that manifest from a verification body,
- feed it through `validate_verification_manifest_reference()`,
- assert success for the unmodified round trip,
- then mutate a field and assert the expected failure.

Purpose:

- close the producer→consumer integration gap for manifest semantics.

### 2. Centralize base-ref helpers

Planned direction:

- move `git_ref_exists` and `resolve_base_ref` into `scripts/governance_rules.py`,
- update:
  - `scripts/all_green_gate.py`
  - `scripts/validate_issue_links.py`
  - `scripts/validate_issues.py`
- replace local helper implementations with shared imports or thin wrappers,
- reduce duplicated helper testing by shifting to:
  - direct shared-helper tests,
  - minimal caller integration checks.

Purpose:

- remove duplicated shared logic and reduce drift pressure.

### 3. Continue remaining checklist rows in order

Likely next stabilization targets after the two items above:

- ratify and reconcile changed-path skip policy,
- define explicit validator ownership boundaries,
- verify RED_TAG derivation end-to-end,
- reconcile gate execution semantics,
- choose and implement one main deterministic integration proof for the stabilized governance flow.

## Current working definition of done

The working definition of done is:

- each frozen governance control surface has one canonical implementation path,
- duplicate/superseded/shadowed behavior has been reconciled or explicitly deferred,
- docs, tests, and implementation agree on the retained contract,
- deterministic integration proof exists for the stabilized flow,
- freeze-exit evidence is recorded,
- no unresolved drift remains across the frozen control surfaces.

In practical terms, we are **not done** when a checklist row merely has a diagnosis. We are done only when rows are either:

- `verified`, or
- explicitly deferred through linked follow-up issues.

The freeze remains active until:

- a reviewed canonical contract revision is merged,
- validators/gate/tests align with the revised contract,
- and no unresolved drift remains across the affected control surfaces.

## Where this work is documented

### Problem diagnosis
- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`

### Freeze / canonical contract during stabilization
- `docs/issues/governance-control-surface-contract-freeze.md`

### Execution tracker / current stabilization state
- `docs/issues/evidence/governance-stabilization-checklist.md`

### Workflow-level notice and reference
- `docs/issues.md`

## Current status statement

We are no longer in open-ended diagnosis.

We are now in controlled stabilization with:

- documented drift diagnosis,
- active contract freeze,
- active stabilization checklist,
- ratified analysis decisions for:
  - verification manifest semantics,
  - shared base-ref helper consolidation,
- and a bounded next-step plan focused on:
  - manifest round-trip proof,
  - helper centralization,
  - remaining surface reconciliation.

The repository is **in stabilization, not yet in verified convergence**.
