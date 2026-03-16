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
| Shared governance rules | `scripts/governance_rules.py` | decision made | partial (helper behavior is duplicated consistently across scripts, but tests currently validate per-script copies rather than one authoritative shared implementation path) | yes (`git_ref_exists` and `resolve_base_ref` are duplicated in `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py`; `git_ref_exists` shows no meaningful divergence, and `resolve_base_ref` differs only in caller-facing degraded-mode note wording) | **Canonical decision (analysis ratified):** centralize base-ref resolution primitives in `scripts/governance_rules.py`. Keep one shared behavioral implementation for `git_ref_exists` and `resolve_base_ref`; allow only thin caller wrappers if caller-specific note wording must remain different. | replace local helper implementations in `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py` with shared imports or thin wrappers; move duplicated helper tests toward direct shared-helper coverage plus minimal caller integration checks | ☐ |
| Issue schema/state model | `docs/issues.md`, `scripts/validate_issues.py` | inventory complete | mostly yes for `triage_intake` / `governed_execution` and transition semantics | possible edge drift (status/state enforcement details may differ across docs/tests) | TBD | compare enforced transitions and allowed statuses in docs vs validator tests; record any mismatch as explicit reconcile item | ☐ |
| Issue-link / reference validation | `scripts/validate_issue_links.py` | inventory complete | partial (manifest-link and reference checks exist, but ownership boundary vs schema validator is not yet fully explicit) | likely (overlap with schema/state checks and manifest semantics) | TBD | document exact boundary: what link validator owns vs what issue-schema validator owns; eliminate ambiguity | ☐ |
| RED_TAG derivation | `scripts/generate_red_tag_index.py`, `docs/issues/RED_TAG.md` | inventory complete | mostly yes on generated-file expectation and severity-driven derivation | possible (metadata coupling still needs explicit audit) | TBD | verify generated-only flow end-to-end, including validator expectations and no hand-edited policy drift | ☐ |
| Gate profiles | `scripts/all_green_gate.py`, `docs/testing.md`, `README.md` | inventory complete | partial (triage/readiness semantics are documented but need consistency audit against gate implementation/tests) | likely (profile-local behavior vs shared governance check surfaces) | TBD | inventory profile behavior, ensure one canonical check path per profile, and reconcile docs/examples with implementation | ☐ |
| Changed-path skip policy | `scripts/all_green_gate.py` | inventory complete | partial (freeze contract specifies governed-surface full-check behavior; current baseline still relies on first-pass skip scopes only) | likely (governed-path matrix remains implicit in code and not yet ratified as canonical ownership boundary) | **Proposed canonical decision (analysis-only, not yet ratified):** governed control-surface changes disable skip reduction; full governance checks run; skip reasons remain visible; non-governed-only changes may remain eligible for deterministic skip policy; no skip rule bypasses manifest/issue/RED_TAG validation when governed surfaces are touched. | after canonical decision ratification under the active freeze, update `scripts/all_green_gate.py` to add explicit governed-surface path matrix + short-circuit in `apply_governance_skip_policy`, add deterministic test coverage in `tests/test_all_green_gate.py`, and then rerun canonical gate to prove behavior; in this step, keep implementation unchanged | ☐ |
| Feature-status / issue linkage | `docs/qa/feature-status.yaml`, `scripts/report_feature_status.py`, `scripts/suggest_issue_links.py` | inventory complete | partial (linkage contract exists; fallback/implicit behavior still needs conformance check) | possible (explicit linkage and suggestion fallback may overlap) | TBD | verify canonical linkage contract and document fallback precedence; align fixtures/examples if needed | ☐ |
| Verification manifest semantics | `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `artifacts/verification/*` | decision made | yes for ownership boundary (producer vs reference validator vs schema/state validator) | partial (manifest ownership boundary is clean; remaining risk is missing producer→consumer round-trip proof) | **Canonical decision (analysis ratified):** `scripts/all_green_gate.py` owns manifest production only; `scripts/validate_issue_links.py` owns manifest reference integrity end-to-end (path/run-ID/file existence/JSON/required checks); `scripts/validate_issues.py` owns only section/schema/state policy and does not parse manifest payload semantics. | add a deterministic round-trip contract test that feeds `write_verification_manifest()` output into `validate_verification_manifest_reference()` | ☐ |
| Triage routing | `scripts/triage_router.py`, `docs/qa/triage-routing.yaml` | inventory complete | unknown pending router-consumer contract audit | possible (risk of reinterpreting upstream gate semantics) | TBD | verify router consumes stabilized outputs without semantic reinterpretation; align routing config docs/tests | ☐ |
| Integration proof | relevant tests under `tests/` | inventory complete | unknown (deterministic multi-surface proof not yet selected) | N/A | TBD | select one deterministic boundary test (gate -> validators or issue -> manifest linkage) and define expected assertions | ☐ |

## Duplicate / superseded path audit

Record any duplicate, superseded, shadowed, or partially overlapping behavior found during stabilization.

| Area | Suspected source PR(s) | Finding | Canonical retained path | Removal / reconciliation needed | Done |
| --- | --- | --- | --- | --- | --- |
| Manifest/reference handling | `#487`, `#488` | Inspection confirmed no hidden manifest-validation path in `scripts/validate_issues.py`; manifest/reference integrity checks are implemented in `scripts/validate_issue_links.py`; gate writes verification manifests but does not validate/interpret them. Tests mirror this split, but producer/consumer coupling is indirect and currently misses a direct round-trip assertion. | **Retained canonical path:** `scripts/all_green_gate.py` owns manifest production; `scripts/validate_issue_links.py` owns existence/run-ID/reference integrity for manifests cited by issue files; `scripts/validate_issues.py` owns only issue-schema/state policy and must not become a second manifest-link validator. Shared parsing helpers may live in `scripts/governance_rules.py`, but not duplicated acceptance logic. | Keep boundary as-is; add one contract test for producer→consumer manifest compatibility (round trip). | ☐ |
| Base-ref resolution helpers | pre-existing; reviewed during `#481`–`#489` stabilization | Inspection confirmed duplicate production implementations of `git_ref_exists` and `resolve_base_ref` in `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, and `scripts/validate_issues.py`. `git_ref_exists` is functionally identical aside from variable naming; `resolve_base_ref` has the same control flow and fallback order, with only caller-facing degraded-mode note wording differing. Tests currently assert per-script helper behavior rather than one shared implementation path. | One shared core implementation in `scripts/governance_rules.py`; caller-specific wrappers only if degraded-mode note wording must remain specialized by script context. | Centralize `git_ref_exists` and `resolve_base_ref` into `governance_rules.py`, update all three scripts to import the shared helpers or thin wrappers, and replace duplicated per-script helper tests with direct shared-helper tests plus minimal caller integration coverage. | ☐ |
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

# pass-three manifest/reference ownership and call-path inspection
sed -n '130,220p' scripts/all_green_gate.py
sed -n '340,450p' scripts/validate_issue_links.py
sed -n '1,220p' scripts/validate_issues.py
sed -n '1,220p' scripts/governance_rules.py
rg -n "validate_verification_manifest_reference|Verification" scripts/validate_issue_links.py scripts/validate_issues.py
rg -n '"run_id"|"checks"|manifest_path|required checks|missing required checks' scripts/all_green_gate.py scripts/validate_issue_links.py tests/test_all_green_gate.py tests/test_validate_issue_links.py
sed -n '180,430p' tests/test_validate_issue_links.py
sed -n '450,520p' tests/test_all_green_gate.py
sed -n '100,170p' tests/test_validate_issues.py
rg -n "artifacts/verification|run_id|Verification manifest|Run ID|checks" scripts/validate_issues.py
rg -n "read_text|json.loads|artifacts/verification|run_id|checks" scripts/all_green_gate.py
rg -n "^def " scripts/all_green_gate.py scripts/validate_issue_links.py scripts/validate_issues.py scripts/governance_rules.py
rg -n "^from scripts|^import scripts|governance_rules" scripts/all_green_gate.py scripts/validate_issue_links.py scripts/validate_issues.py

# pass-four shared-helper duplication inspection
grep -r resolve_base_ref *
grep -r git_ref_exists *
sed -n '/def git_ref_exists/,/^$/p' scripts/all_green_gate.py
sed -n '/def git_ref_exists/,/^$/p' scripts/validate_issue_links.py
sed -n '/def git_ref_exists/,/^$/p' scripts/validate_issues.py
diff -u <(sed -n '/def git_ref_exists/,/^$/p' scripts/all_green_gate.py) <(sed -n '/def git_ref_exists/,/^$/p' scripts/validate_issue_links.py)
nl -ba scripts/all_green_gate.py | sed -n '217,260p'
nl -ba scripts/validate_issue_links.py | sed -n '131,175p'
nl -ba scripts/validate_issues.py | sed -n '81,125p'
rg -n "def test_resolve_base_ref|git_ref_exists|resolve_base_ref" tests/test_all_green_gate.py tests/test_validate_issue_links.py tests/test_validate_issues.py
```

### Notes

- First pass intentionally limited to inventory fields (`Current status`, `Docs/tests agree?`, `Duplicate/conflict?`, `Action needed`) with no code-path edits.
- Canonical decision, reconciliation, and verification rows remain open for subsequent stabilization passes.
- Pass two (role-separated @platform-qa and @release-governance review) is now analysis-only for Changed-path skip policy: implementation/test state was inspected against freeze contract, and canonical wording is captured as a proposed decision pending reconciliation authority.
- Pass two manifest/reference audit is analysis-only: provisional ownership boundary is production in `scripts/all_green_gate.py`, manifest reference integrity in `scripts/validate_issue_links.py`, and schema/state policy in `scripts/validate_issues.py`.
- Pass three ownership/call-path inspection confirmed the manifest/reference boundary above, found no manifest parsing/validation logic in `scripts/validate_issues.py`, and identified the remaining manifest-related reconciliation item: missing producer→consumer round-trip manifest contract test.
- Pass four shared-helper inspection confirmed duplicate production implementations of `git_ref_exists` and `resolve_base_ref` across `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py`. `git_ref_exists` is functionally identical; `resolve_base_ref` shares the same control flow and fallback order, with only caller-facing degraded-mode note wording differing. Current tests validate per-script helper copies rather than a single shared helper path.

## Freeze-exit recommendation

Mark ready only when all rows above are either `verified` or explicitly deferred via linked follow-up issue.

- [ ] Ready to recommend freeze lift
- [x] Not ready
