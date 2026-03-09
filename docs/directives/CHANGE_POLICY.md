# Directive Change Policy

This policy defines how directive artifacts are versioned and changed. It applies to all updates under `docs/directives/`.

## Canonical references

The following directive documents are canonical references and must be treated as the source of truth when processing directive changes:

- `docs/invariants.md` (invariant index and migration boundary)
- `docs/invariants/answer-policy.md` (canonical response-policy invariant registry)
- `docs/invariants/pipeline.md` (canonical pipeline semantics invariant registry)
- `docs/directives/source-map.md`
- `docs/directives/terms.md`
- `docs/directives/traceability-matrix.md`

`docs/directives/invariants.md` is a required mirror of the canonical sync block in `docs/invariants/answer-policy.md` and must not diverge on invariant IDs, invariant statements, or scenario-ID mappings.

If a change conflicts with these references, either:

1. update the relevant canonical reference in the same pull request, or
2. block the directive change until canonical references are aligned.

## Invariant update order and sync check

For any invariant change, apply updates in this order:

1. Edit the appropriate canonical source first:
   - `docs/invariants/answer-policy.md` for response-policy invariant changes.
   - `docs/invariants/pipeline.md` for stage semantics and anti-projection changes.
   - `docs/invariants.md` to maintain index/migration-boundary guidance when scope changes.
2. Run `python scripts/sync_invariants_mirror.py` to refresh `docs/directives/invariants.md` from the canonical sync block.
3. Run `python scripts/sync_invariants_mirror.py --check` (or `python scripts/validate_invariant_sync.py`) and ensure it passes before merge.

The sync check is a merge gate for invariant-related changes.

## Semantic versioning policy for terms and invariants

Directive changes affecting terms or invariants must use semantic versioning labels in the pull request description and commit message footer.

Version impact rules:

- **PATCH**: non-behavioral editorial fixes (spelling, formatting, clarification with no meaning change).
- **MINOR**: backward-compatible additions (new term, new invariant, new traceability row, added rationale) that do not invalidate existing behavior.
- **MAJOR**: breaking changes (term meaning change, invariant removal, invariant tightening/loosening that changes expected behavior, or fallback/contract interpretation changes).

Required notation:

- Include `Directive-SemVer: PATCH|MINOR|MAJOR` in the PR body.
- Include a matching commit footer line: `Directive-SemVer: PATCH|MINOR|MAJOR`.

If multiple directive changes exist in one PR, use the highest required bump.

## Required PR justification fields for directive changes

Any pull request that changes directive docs must include all fields below:

- `Directive-SemVer`: `PATCH`, `MINOR`, or `MAJOR`.
- `Change-Type`: one of `term`, `invariant`, `traceability`, `bdd`, `editorial` (comma-separated if multiple).
- `Canonical-Refs-Updated`: `yes` or `no`.
- `Justification`: why this change is needed now.
- `Behavior-Impact`: explicit statement of runtime/acceptance impact.
- `Migration-Notes`: required follow-up actions for contributors/operators.
- `Validation-Evidence`: commands or checks run to validate consistency.

Missing fields are a merge blocker.

## Mandatory traceability and BDD updates

When a directive changes, the same PR must update linked artifacts to preserve end-to-end traceability.

- If a **term** changes in meaning or scope, update:
  - `docs/directives/terms.md`, and
  - any impacted rows in `docs/directives/source-map.md` and `docs/directives/traceability-matrix.md`.
- If an **invariant** is added/changed/removed, update:
  - `docs/directives/invariants.md`,
  - impacted directive mappings in `docs/directives/traceability-matrix.md`, and
  - relevant BDD scenarios under `features/*.feature`.
- If runtime behavior contract changes, update:
  - BDD scenario IDs and/or scenarios to reflect new expected behavior,
  - step assertions in `features/steps/*.py` when applicable,
  - traceability links so each changed directive still maps to enforcement, tests, and evidence.

A directive change is incomplete unless traceability matrix entries and BDD scenarios remain synchronized.

## Review and merge gate

Before merge, reviewers must confirm:

1. semantic version label matches the highest-impact directive change,
2. all required PR justification fields are present,
3. canonical references are aligned,
4. traceability matrix and BDD scenarios were updated where required.

If any check fails, the PR should be returned for revision.
