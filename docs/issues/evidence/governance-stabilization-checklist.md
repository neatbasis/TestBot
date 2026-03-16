# Governance stabilization checklist

> Status: Active during temporary freeze
>
> Governing contract: `docs/issues/governance-control-surface-contract-freeze.md`
>
> Parent issue: `ISSUE-0022`
>
> Designated stabilization owner: `@platform-qa`
>
> Reviewer / contract authority: `@release-governance`

## Purpose

Track stabilization progress for frozen governance control surfaces after PRs `#481`–`#489`.

Use this checklist to inventory current behavior, identify overlap/drift, choose one canonical implementation path per surface, and record convergence status.

## Status legend

- `not reviewed`
- `inventory complete`
- `decision made`
- `reconciled`
- `verified`

## Surface checklist

| Surface | Canonical file(s) | Current status | Docs/tests agree? | Duplicate/conflict? | Canonical decision | Action needed | Done |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Shared governance rules | `scripts/governance_rules.py` | inventory complete | partial (shared-rule intent is documented; validator ownership boundaries still need explicit reconciliation) | likely (rule intent is shared across multiple validators) | TBD | map every rule primitive consumer (`validate_issues`, `validate_issue_links`, gate callers) and flag any duplicated inline checks | ☐ |
| Issue schema/state model | `docs/issues.md`, `scripts/validate_issues.py` | inventory complete | mostly yes for `triage_intake` / `governed_execution` and transition semantics | possible edge drift (status/state enforcement details may differ across docs/tests) | TBD | compare enforced transitions and allowed statuses in docs vs validator tests; record any mismatch as explicit reconcile item | ☐ |
| Issue-link / reference validation | `scripts/validate_issue_links.py` | inventory complete | partial (manifest-link and reference checks exist, but ownership boundary vs schema validator is not yet fully explicit) | likely (overlap with schema/state checks and manifest semantics) | TBD | document exact boundary: what link validator owns vs what issue-schema validator owns; eliminate ambiguity | ☐ |
| RED_TAG derivation | `scripts/generate_red_tag_index.py`, `docs/issues/RED_TAG.md` | inventory complete | mostly yes on generated-file expectation and severity-driven derivation | possible (metadata coupling still needs explicit audit) | TBD | verify generated-only flow end-to-end, including validator expectations and no hand-edited policy drift | ☐ |
| Gate profiles | `scripts/all_green_gate.py`, `docs/testing.md`, `README.md` | inventory complete | partial (triage/readiness semantics are documented but need consistency audit against gate implementation/tests) | likely (profile-local behavior vs shared governance check surfaces) | TBD | inventory profile behavior, ensure one canonical check path per profile, and reconcile docs/examples with implementation | ☐ |
| Changed-path skip policy | `scripts/all_green_gate.py` | inventory complete | partial (freeze contract specifies governed-surface full-check behavior; current baseline still relies on first-pass skip scopes only) | likely (governed-path matrix remains implicit in code and not yet ratified as canonical ownership boundary) | **Proposed canonical decision (analysis-only, not yet ratified):** governed control-surface changes disable skip reduction; full governance checks run; skip reasons remain visible; non-governed-only changes may remain eligible for deterministic skip policy; no skip rule bypasses manifest/issue/RED_TAG validation when governed surfaces are touched. | after canonical decision ratification under the active freeze, update `scripts/all_green_gate.py` to add explicit governed-surface path matrix + short-circuit in `apply_governance_skip_policy`, add deterministic test coverage in `tests/test_all_green_gate.py`, and then rerun canonical gate to prove behavior; in this step, keep implementation unchanged | ☐ |
| Feature-status / issue linkage | `docs/qa/feature-status.yaml`, `scripts/report_feature_status.py`, `scripts/suggest_issue_links.py` | inventory complete | partial (linkage contract exists; fallback/implicit behavior still needs conformance check) | possible (explicit linkage and suggestion fallback may overlap) | TBD | verify canonical linkage contract and document fallback precedence; align fixtures/examples if needed | ☐ |
| Verification manifest semantics | `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `artifacts/verification/*` | inventory complete | partial (required checks + run-ID linkage are represented in tests, needs full doc/code fixture parity pass) | likely (manifest/reference handling overlap across gate + validators) | TBD | audit manifest schema/required fields/run-ID linkage/failure behavior and remove any duplicate superseded handling path | ☐ |
| Triage routing | `scripts/triage_router.py`, `docs/qa/triage-routing.yaml` | inventory complete | unknown pending router-consumer contract audit | possible (risk of reinterpreting upstream gate semantics) | TBD | verify router consumes stabilized outputs without semantic reinterpretation; align routing config docs/tests | ☐ |
| Integration proof | relevant tests under `tests/` | inventory complete | unknown (deterministic multi-surface proof not yet selected) | N/A | TBD | select one deterministic boundary test (gate -> validators or issue -> manifest linkage) and define expected assertions | ☐ |

## Duplicate / superseded path audit

Record any duplicate, superseded, shadowed, or partially overlapping behavior found during stabilization.

| Area | Suspected source PR(s) | Finding | Canonical retained path | Removal / reconciliation needed | Done |
| --- | --- | --- | --- | --- | --- |
| Manifest/reference handling | `#487`, `#488` | Potential overlap between manifest production (`all_green_gate`) and manifest reference/link validation (`validate_issue_links`) plus schema ownership boundaries. | TBD | Confirm one canonical manifest semantics owner per concern (production vs validation vs schema constraints) and remove shadow checks. | ☐ |
| Gate execution semantics | `#482`, `#486`, `#489` | Profile semantics, changed-path skip behavior, and downstream routing consumption appear tightly coupled and order-sensitive. | TBD | Freeze one canonical execution order with explicit skip/force rules and ensure router consumes, not reinterprets. | ☐ |
| Issue/reference semantics | `#481`, `#483`, `#487`, `#488` | Issue schema/state enforcement and link/reference enforcement may partially overlap across validators. | TBD | Declare validator ownership boundaries and retire duplicate checks where equivalent. | ☐ |
| RED_TAG / issue metadata coupling | `#483`, `#484` | Derivation depends on canonical issue metadata; coupling exists with issue-state/severity semantics and validator expectations. | TBD | Verify generated index exactly reflects issue metadata contract; reconcile any conflicting assumptions. | ☐ |

## Integration proof plan

Document the deterministic proof that the stabilized control surfaces behave coherently end-to-end.

### Candidate interaction boundary

- [x] gate -> validators
- [x] issue record -> manifest reference validation
- [x] governed-path change disables skip reduction
- [x] triage routing consumes stabilized gate output without reinterpretation
- [ ] other: `________________`

### Planned test artifact(s)

- `tests/test_all_green_gate.py`
- `tests/test_validate_issue_links.py`

## Evidence log

### Commands

```bash
# first-pass inventory commands
sed -n '1,260p' docs/issues/governance-control-surface-contract-freeze.md
sed -n '1,260p' docs/issues/evidence/coordination-failure-contract-drift-matrix.md
rg -n "triage_intake|governed_execution|RED_TAG|manifest|triage|readiness|skip|verification|triage routing|Severity: red" docs/issues.md scripts/all_green_gate.py scripts/validate_issues.py scripts/validate_issue_links.py scripts/governance_rules.py scripts/triage_router.py docs/qa/triage-routing.yaml docs/testing.md README.md tests/test_all_green_gate.py tests/test_validate_issue_links.py tests/test_validate_issues.py

# pass-two analysis-only inspection commands (no implementation edits)
rg -n "GOVERNED_SURFACE_|apply_governance_skip_policy|skip_reason|force_full_governance" scripts/all_green_gate.py
rg -n "disables_skip_reduction_for_governed_surface_changes|apply_governance_skip_policy" tests/test_all_green_gate.py
sed -n '1,260p' docs/issues/governance-control-surface-contract-freeze.md
```

### Notes

- First pass intentionally limited to inventory fields (`Current status`, `Docs/tests agree?`, `Duplicate/conflict?`, `Action needed`) with no code-path edits.
- Canonical decision, reconciliation, and verification rows remain open for subsequent stabilization passes.
- Pass two (role-separated @platform-qa and @release-governance review) is now analysis-only for Changed-path skip policy: implementation/test state was inspected against freeze contract, and canonical wording is captured as a proposed decision pending reconciliation authority.

## Freeze-exit recommendation

Mark ready only when all rows above are either `verified` or explicitly deferred via linked follow-up issue.

- [ ] Ready to recommend freeze lift
- [x] Not ready
