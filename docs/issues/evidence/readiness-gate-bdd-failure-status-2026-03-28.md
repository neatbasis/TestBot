# Readiness gate BDD failure status (2026-03-28)

## Purpose

Capture the pre-existing `behave` gate debt referenced during PR #659 review so the debt is tracked as issue-linked evidence (not only PR prose).

## Scope of the failure record

- Canonical command context: `python scripts/all_green_gate.py`
- Blocking gate check: `product_behave`
- Failure class (as recorded in PR #659 discussion): pre-existing BDD regressions unrelated to the narrow CLI entrypoint normalization change.

## Failing BDD feature/module names

`product_behave` in this repository is the canonical BDD aggregation over the product feature modules below; these are the modules that require explicit remediation ownership for this debt cycle:

1. `features/testbot/answer_contract.feature`
2. `features/testbot/memory_recall.feature`
3. `features/testbot/intent_grounding.feature`

## Failure-type classification (triage bucket)

- `features/testbot/answer_contract.feature`: logic regression bucket (assertion mismatch in behavior contract paths).
- `features/testbot/memory_recall.feature`: logic regression bucket (continuity/recall behavior drift).
- `features/testbot/intent_grounding.feature`: logic regression bucket (routing/intent classification drift).

Current classification is explicitly **not** a missing-dev-dependency preflight failure (`behave` missing) and **not** marked as flaky in governance records; treat as deterministic behavior debt until reclassified with fresh evidence.

## Why PR #659 was acceptable as a narrow merge

- PR #659 scope was limited to canonical entrypoint normalization and startup Ask-channel messaging hardening.
- The failing `product_behave` debt predated that scope and was already tracked in open issue streams.
- Merge acceptability was therefore "narrow-change acceptable with linked pre-existing debt", not "readiness gate clean".

## Linked remediation ownership

- Primary runtime remediation anchor: `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- Behavioral blocker linkage: `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- Governance close-order linkage: `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`

## Blocking vs non-blocking interpretation

- For canonical merge/readiness interpretation: **blocking** (BDD is mandatory by `docs/testing.md`).
- For narrowly-scoped compatibility/governance PRs with no feature-behavior broadening: may be treated as **known pre-existing debt** only when this evidence note and linked issue ownership remain current.

## Next action

1. Re-run `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`.
2. Refresh this note with current failing scenario names from the generated BDD output.
3. Keep ISSUE-0013/0014/0015 cross-links synchronized with the refreshed artifact timestamp.
