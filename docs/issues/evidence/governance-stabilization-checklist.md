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
| Changed-path skip policy | `scripts/all_green_gate.py` | reconciled | mostly yes (freeze-governed full-check override is implemented in `all_green_gate.py` and covered by deterministic tests; keep governed-surface matrix aligned with freeze contract as surfaces evolve) | resolved in code; ongoing risk is future governed-surface drift if the matrix is not kept in sync with freeze-defined surfaces | **Canonical decision (implemented):** if any freeze-governed control-surface file or governed semantic fixture/config changes, path-based skip reduction is disabled and full governance checks run; non-governed-only changes may still use deterministic skip reduction; reason visibility remains explicit. | record PR `#501` as implementation evidence and keep governed-surface matrix synchronized with freeze-defined surfaces | ☐ |
| Feature-status / issue linkage | `docs/qa/feature-status.yaml`, `scripts/report_feature_status.py`, `scripts/suggest_issue_links.py` | inventory complete | partial (linkage contract exists; fallback/implicit behavior still needs conformance check) | possible (explicit linkage and suggestion fallback may overlap) | TBD | verify canonical linkage contract and document fallback precedence; align fixtures/examples if needed | ☐ |
| Verification manifest semantics | `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `artifacts/verification/*` | reconciled | yes for ownership boundary and round-trip sufficiency (producer vs reference validator vs schema/state validator contracts are covered) | resolved for current contract boundary; producer→consumer round-trip proof exists in tests | **Canonical decision (analysis ratified):** `scripts/all_green_gate.py` owns manifest production only; `scripts/validate_issue_links.py` owns manifest reference integrity end-to-end (path/run-ID/file existence/JSON/required checks); `scripts/validate_issues.py` owns only section/schema/state policy and does not parse manifest payload semantics. | record existing round-trip coverage as implementation evidence and keep producer/consumer contract assertions current | ☐ |
| Triage routing | `scripts/triage_router.py`, `docs/qa/triage-routing.yaml` | inventory complete | unknown pending router-consumer contract audit | possible (risk of reinterpreting upstream gate semantics) | TBD | verify router consumes stabilized outputs without semantic reinterpretation; align routing config docs/tests | ☐ |
| Integration proof | relevant tests under `tests/` | inventory complete | unknown (deterministic multi-surface proof not yet selected) | N/A | TBD | select one deterministic boundary test (gate -> validators or issue -> manifest linkage) and define expected assertions | ☐ |

## Duplicate / superseded path audit

Record any duplicate, superseded, shadowed, or partially overlapping behavior found during stabilization.

| Area | Suspected source PR(s) | Finding | Canonical retained path | Removal / reconciliation needed | Done |
| --- | --- | --- | --- | --- | --- |
| Manifest/reference handling | `#487`, `#488` | Inspection confirmed no hidden manifest-validation path in `scripts/validate_issues.py`; manifest/reference integrity checks are implemented in `scripts/validate_issue_links.py`; gate writes verification manifests but does not validate/interpret them. Tests mirror this split, and a direct generated-manifest round-trip proof now exists in tests. | **Retained canonical path:** `scripts/all_green_gate.py` owns manifest production; `scripts/validate_issue_links.py` owns existence/run-ID/reference integrity for manifests cited by issue files; `scripts/validate_issues.py` owns only issue-schema/state policy and must not become a second manifest-link validator. Shared parsing helpers may live in `scripts/governance_rules.py`, but not duplicated acceptance logic. | Keep boundary as-is; maintain the round-trip contract test and update it only if manifest schema/validator expectations change. | ☐ |
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

# pass-five reconciliation evidence (PR #501 and manifest round-trip sufficiency)
rg -n "GOVERNED_SURFACE_PATH_PREFIXES|apply_governance_skip_policy|force_full_governance" scripts/all_green_gate.py
rg -n "governed_surface|skip_reduction|force_full_governance" tests/test_all_green_gate.py
rg -n "write_verification_manifest|validate_verification_manifest_reference|verification_manifest" tests/test_all_green_gate.py tests/test_validate_issue_links.py
```

### Notes

- First pass intentionally limited to inventory fields (`Current status`, `Docs/tests agree?`, `Duplicate/conflict?`, `Action needed`) with no code-path edits.
- Canonical decision, reconciliation, and verification rows remain open for subsequent stabilization passes.
- Pass two (role-separated @platform-qa and @release-governance review) is an analysis-only historical snapshot for Changed-path skip policy: implementation/test state was inspected against freeze contract, and canonical wording was captured as a proposed decision at that time (superseded by pass-five reconciliation evidence).
- Pass two manifest/reference audit is analysis-only: provisional ownership boundary is production in `scripts/all_green_gate.py`, manifest reference integrity in `scripts/validate_issue_links.py`, and schema/state policy in `scripts/validate_issues.py`.
- Pass three ownership/call-path inspection confirmed the manifest/reference boundary above and found no manifest parsing/validation logic in `scripts/validate_issues.py`; its temporary gap note about producer→consumer round-trip proof is superseded by pass-five evidence that existing tests satisfy the contract.
- Pass four shared-helper inspection confirmed duplicate production implementations of `git_ref_exists` and `resolve_base_ref` across `all_green_gate.py`, `validate_issue_links.py`, and `validate_issues.py`. `git_ref_exists` is functionally identical; `resolve_base_ref` shares the same control flow and fallback order, with only caller-facing degraded-mode note wording differing. Current tests validate per-script helper copies rather than a single shared helper path.
- Pass five recorded implementation reconciliation on `main`: changed-path skip-policy behavior is now implemented (governed-surface matrix + full-check override) and covered by deterministic `tests/test_all_green_gate.py` coverage; checklist wording now reflects reconciled status.
- Pass five also confirmed manifest round-trip proof is already present on `main` via existing tests, so the remaining manifest gap is closed; action shifts to preserving current contract coverage as schema/validator expectations evolve.

## Freeze-exit recommendation

Mark ready only when all rows above are either `verified` or explicitly deferred via linked follow-up issue.

- [ ] Ready to recommend freeze lift
- [x] Not ready
