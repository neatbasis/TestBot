# CRAAP analysis: governance documentation vs committed governance changes

> Scope reviewed:
>
> - `docs/issues/evidence/governance-stabilization-checklist.md`
> - `docs/issues/governance-control-surface-contract-freeze.md`
> - `docs/issues.md`
> - Related implementation anchors in `scripts/` and commit history
>
> Baseline note: this repository snapshot has no local `main` branch ref; analysis uses currently committed history in this checkout as the available baseline for "changes committed to main" claims.

## Method

1. Inspect current contract/checklist/workflow documents for explicit governance claims.
2. Inspect recent commit history touching those documents.
3. Spot-check validator/gate code paths for contract alignment on the highest-risk surfaces:
   - state/status enforcement,
   - base-ref fallback semantics,
   - verification-manifest ownership,
   - changed-path skip-policy guardrails.
4. Rate each CRAAP dimension (Currency, Relevance, Authority, Accuracy, Purpose).

## CRAAP summary scorecard

| Dimension | Rating | Summary |
| --- | --- | --- |
| Currency | **Strong** | Core docs show same-week updates tied to ISSUE-0022 stabilization commits. |
| Relevance | **Strong** | Documents map directly to active governance control surfaces and frozen contract obligations. |
| Authority | **Strong** | Freeze contract explicitly defines precedence and designated ownership/review authority. |
| Accuracy | **Strong** | High-risk governance claims were directly verified across four targeted surfaces with command-level and test-level evidence recorded in pass-seven logs. |
| Purpose | **Strong** | Documents are policy/operational controls with explicit anti-drift intent and measurable workflows. |

## Claim investigation map (supporting vs weakening sources)

The table below identifies where each major claim is best supported and which files currently weaken confidence (for example because they explicitly show unresolved stabilization work, caveats, or environment constraints).

| Claim under review | Supporting sources | Sources that weaken confidence / show unresolved risk | How accuracy can be investigated |
| --- | --- | --- | --- |
| Freeze contract is authoritative and precedence is explicit. | `docs/issues/governance-control-surface-contract-freeze.md` (purpose, precedence, authority, protocol), `docs/issues.md` (freeze notice linkage). | `docs/issues/evidence/governance-stabilization-checklist.md` still marks several surfaces as `inventory complete`/`TBD`, showing convergence is incomplete even with clear authority. | Confirm precedence language and role assignments in docs, then verify no conflicting semantics in downstream docs/tests for the same surfaces. |
| Issue status/state model is reconciled and enforced. | `docs/issues.md` status/state matrix; `scripts/validate_issues.py` constants + transition matrix; `tests/test_validate_issues.py` deterministic enforcement coverage. | Checklist non-blocking edge-case note for vocabulary-vs-transition rejection ordering indicates behavior is compliant but not maximally diagnostic. | Compare matrix rows in docs to validator constants and run deterministic tests that assert allowed/disallowed combinations. |
| Base-ref fallback behavior is consistent across governance surfaces. | `docs/issues.md` fallback workflow; `scripts/governance_rules.py` canonical fallback order/notes; validator args in `scripts/validate_issue_links.py` and `scripts/validate_issues.py`. | `scripts/validate_issue_links.py` intentionally fails closed for commit traceability when requested ref degrades (unless explicit opt-in), which can look like doc/code mismatch if this stricter behavior is not accounted for in interpretation. | Execute validators with and without `origin/main` availability and compare emitted notes/failures against documented fallback expectations and strictness boundaries. |
| Changed-path skip policy cannot silently bypass governed checks. | `docs/issues/governance-control-surface-contract-freeze.md` changed-path rule; `scripts/all_green_gate.py` governed-surface path scopes + force-full checks; `tests/test_all_green_gate.py` policy tests. | Checklist row remains `reconciled` with ongoing action to keep governed-surface matrix synchronized as surfaces evolve (drift risk acknowledged). | Inspect governed-surface scope lists and run gate tests that assert full-governance behavior when governed files change. |
| Verification manifest contract ownership is converged producer↔consumer. | `docs/issues.md` verification-manifest guidance; `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `scripts/verification_manifest_contract.py`; `tests/test_validate_issue_links.py` and `tests/test_all_green_gate.py`. | Checklist still indicates adjacent ownership boundary work remains open in other rows (issue-link/reference overlap and RED_TAG coupling), so convergence is strong for manifest payload semantics but broader governance ownership is not fully closed. | Trace producer payload construction, consumer validation entrypoints, and required-check assertions through unit tests and sample artifact references. |
| CRAAP conclusions are representative of "changes committed to main." | Commit history for reviewed docs (local `git log` evidence) and current repository state across docs/scripts/tests. | No local `main` ref in this environment; claims about "on main" are inferred from available history in checkout rather than direct local `main` diff comparison. | Record branch/ref availability first, then use available history and file-level cross-checks; repeat in an environment with fetched `origin/main` for authoritative comparison. |

## Files inventory by evidentiary role

### Primary supporting sources

- `docs/issues/governance-control-surface-contract-freeze.md`
- `docs/issues/evidence/governance-stabilization-checklist.md`
- `docs/issues.md`
- `scripts/governance_rules.py`
- `scripts/validate_issues.py`
- `scripts/validate_issue_links.py`
- `scripts/all_green_gate.py`
- `scripts/verification_manifest_contract.py`
- `tests/test_validate_issues.py`
- `tests/test_validate_issue_links.py`
- `tests/test_all_green_gate.py`

### Sources that currently weaken claim strength (or require careful interpretation)

- `docs/issues/evidence/governance-stabilization-checklist.md` (open rows with `inventory complete`, `partial`, `TBD`, and pending actions).
- `docs/issues/evidence/governance-craap-analysis-main-alignment.md` (environment caveat: no local `main` ref).
- `scripts/validate_issue_links.py` (fail-closed commit-traceability behavior on degraded base refs can appear stricter than generic fallback prose if read without policy-boundary context).

These weakening sources do **not** invalidate the contract; they indicate where confidence is conditional, in-progress, or environment-dependent.

## Accuracy investigation workflow (repeatable)

Use this sequence to validate claims in a reproducible way:

1. Confirm reference availability and branch context:
   - `git branch -a`
   - `git rev-parse --abbrev-ref HEAD`
2. Review recent governance-document commit history:
   - `git log --oneline -- docs/issues/evidence/governance-stabilization-checklist.md docs/issues/governance-control-surface-contract-freeze.md docs/issues.md`
3. Cross-check policy claims against implementation anchors:
   - `rg -n "triage_intake|governed_execution|origin/main|HEAD~1|HEAD|allow-degraded-commit-traceability|GOVERNED_SURFACE_" docs/issues.md docs/issues/governance-control-surface-contract-freeze.md scripts/*.py`
4. Validate deterministic enforcement with canonical gate:
   - `python scripts/all_green_gate.py`
5. If authoritative `main` comparison is required, run the same checks after fetching the canonical ref in a non-detached environment.

## Dated verification note

- **2026-03-17 (pass-seven):** Executed explicit verification commands/tests for base-ref helper deduplication, changed-path skip policy, status/state transition matrix, and integration proof boundaries; outcomes and line-number evidence are recorded in `docs/issues/evidence/issue-0022-pass-seven-verification-log.md`.
- Verified closures from pass-seven:
  - base-ref helper duplication closed with centralized `git_ref_exists` and policy-named wrappers;
  - changed-path skip-policy implementation + PR `#501` history evidence + deterministic test coverage;
  - status/state matrix constants + parametrized transition tests pass;
  - integration proof confirms commit-traceability fail-closed default with explicit degraded-mode opt-in.

Open freeze rows remain intentionally in-progress, but the count of genuinely open `TBD` rows in the core surface checklist is **4** (Issue-link/reference validation, RED_TAG derivation, Gate profiles, Feature-status/issue linkage); Integration proof is now closed.

## Detailed CRAAP analysis

### 1) Currency

**Findings**

- The stabilization checklist is actively maintained, with multiple updates on 2026-03-16/17 and ISSUE-0022-tagged reconciliation commits.
- `docs/issues.md` and freeze-contract policy were also recently updated and cross-referenced.

**Assessment**

- Currency is high for the governance-freeze window: documentation reflects ongoing reconciliation work rather than stale one-off notes.

**Residual risk**

- Currency is uneven by surface: some rows remain open (`inventory complete`) and should not be interpreted as settled policy outcomes.

### 2) Relevance

**Findings**

- Freeze contract enumerates the exact governance surfaces under temporary change control (validators, gate, RED_TAG, manifests, routing, tests, fixtures).
- Checklist tracks those same surfaces with status and action fields.
- `docs/issues.md` contains operational workflow semantics for issue-state lifecycle, RED_TAG, duplicate prevention, verification manifests, and validator fallback behavior.

**Assessment**

- Relevance is strong: reviewed artifacts are directly aligned to the governance stabilization mission and to implementation touchpoints.

### 3) Authority

**Findings**

- Freeze contract states itself as canonical and higher precedence during freeze.
- It specifies contract authority and required change-control protocol.
- Checklist names designated stabilization owner and reviewer/authority roles.

**Assessment**

- Authority is strong and explicit; hierarchy and escalation path are clear.

### 4) Accuracy

**Findings**

- Issue-state/status claims in checklist/docs are consistent with validator constants/rules for `triage_intake` and `governed_execution`.
- Base-ref fallback chain (`origin/main -> HEAD~1 -> HEAD`) appears consistently across docs and governance helper/validators.
- Changed-path policy hardening claims are supported by governed-surface skip policy hooks in gate code.
- Checklist itself records unresolved areas (`TBD`, partial agreement), which is accurate as a stabilization artifact but means those surfaces are not yet fully converged.

**Assessment**

- Accuracy is strong: high-risk claims were independently verified with command/test evidence across four governance surfaces, while remaining open rows are explicitly scoped and tracked.

**Verified closed (2026-03-17)**

- **Base-ref helper deduplication + policy wrappers:** no consumer `git_ref_exists` definitions, canonical helper present in `scripts/governance_rules.py`, and policy-named wrappers present in all three consumers; integration proof test passes.
- **Changed-path skip policy:** governed-surface matrices and `apply_governance_skip_policy`/`force_full_governance` path verified by line-level grep and deterministic test coverage (targeted + full suite).
- **Issue status/state matrix:** validator constants + transition matrix present and parametrized allowed/disallowed tests pass.
- **Integration boundary behavior:** `commit_traceability_requires_exact_base_ref` and degraded-mode opt-in flow verified, with fail-closed behavior asserted by targeted tests.

### 5) Purpose

**Findings**

- Documents are clearly designed to prevent governance drift: precedence rules, freeze guardrails, deterministic validation expectations, and explicit freeze-exit conditions.
- `docs/issues.md` emphasizes measurable acceptance criteria and reproducible command-based verification.

**Assessment**

- Purpose is strong and non-ambiguous: governance reliability and traceability, not persuasive or promotional prose.

## Overall conclusion

The governance documentation set is **fit-for-purpose and largely trustworthy for current stabilization work**, with the important caveat that several control surfaces are intentionally still in-progress. The material should be treated as **authoritative for frozen semantics**, while operational decisions on unresolved rows should continue through ISSUE-0022 follow-ups until each surface reaches `verified` or documented deferral.

## Recommended next actions

1. Add a short note in checklist evidence that local verification may run without a local `main` ref (detached/sandbox compatibility framing already exists elsewhere).
2. Prioritize closure of the remaining `inventory complete` rows with explicit canonical decisions.
3. Keep code/doc/test synchronization checks in each ISSUE-0022 follow-up commit to preserve freeze integrity.
