# Alignment Tensions Review (Architecture → Rule Governance → Issue Programs → Feature Specifications → BDD Tests → Evidence)

**Date (UTC):** 2026-03-08  
**Reviewer perspective:** Architecture-first traceability through executable evidence.

## Scope and method

This review inspects the current alignment chain in the following order:

1. Architecture
2. Rule Governance
3. Issue Programs
4. Feature Specifications
5. BDD Tests
6. Evidence

Artifacts reviewed include architecture contracts, directive/governance docs, issue records, feature status contracts, BDD feature files, and current gate/status evidence artifacts.

## Alignment tensions by layer transition

### 1) Architecture → Rule Governance

**Tension A1: Canonical 11-stage architecture is normative, but governance currently validates issue metadata and link integrity more directly than stage-contract conformance.**

- Architecture defines strict canonical stage ordering and invariant doctrine (`observe.turn` through `answer.commit`) with explicit prohibition of early lossy `U -> I` projection.
- Governance checks run and pass for issue-link and issue-structure integrity, but those checks do not by themselves prove that runtime stage boundaries are being honored in current behavior.

**Risk:** A repository can be governance-clean while still architecture-drifting in runtime semantics.

### 2) Rule Governance → Issue Programs

**Tension G1: Canonical pipeline is designated as the primary bug-elimination program (ISSUE-0013), but active red-tag pressure is concentrated in ISSUE-0014/0015 with closure-state ambiguity.**

- ISSUE-0013 is the declared triage anchor but remains `open`/`amber` with many acceptance criteria still partial.
- ISSUE-0015 remains listed as `open`/`red` even though its own acceptance-criteria status section says no acceptance criteria remain open.

**Risk:** Program-level prioritization can appear internally inconsistent (resolved governance hardening outcomes still represented as active red urgency).

### 3) Issue Programs → Feature Specifications

**Tension I1: Feature-status capability slices map unresolved ISSUE-0013 criteria, but not all feature scenarios carry explicit issue/AC trace tags.**

- Feature-status contract explicitly maps canonical pipeline capability slices to unresolved ISSUE-0013 acceptance criteria.
- Some feature scenarios include explicit tags (for example ISSUE/AC tags in `memory_recall.feature`), but this pattern is not uniform across all behavior files.

**Risk:** Traceability from issue-program commitments to scenario-level executable specs is uneven, which complicates auditability of closure claims.

### 4) Feature Specifications → BDD Tests

**Tension F1: Behavior specs exist for key contracts, but canonical gate cannot currently execute BDD due to missing dependency precondition.**

- Feature suite coverage is present across answer contract, memory recall, intent grounding, capabilities, source ingestion, and time awareness.
- Current all-green gate evidence fails at preflight because `behave` is not installed in the environment.

**Risk:** Spec intent is present, but BDD cannot currently serve as active enforcement evidence in this execution context.

### 5) BDD Tests → Evidence

**Tension B1: Evidence artifacts are fresh and machine-generated, but they show “status derivation without behavior execution” under dependency failure.**

- Feature status can be regenerated and reports partial/implemented capability states and unresolved issue criteria.
- Because gate execution now stops at BDD preflight dependency failure, evidence signals for behavior regressions are absent in this run.

**Risk:** Decision-makers may over-read status reports as behavioral confidence when the behavior gate did not actually run.

## Cross-cutting tension summary

1. **Conformance asymmetry:** architecture conformance is harder to prove than governance conformance.
2. **Program state ambiguity:** red-tag lifecycle semantics can conflict with acceptance-criteria completion notes.
3. **Traceability granularity gap:** feature-level tags are not consistently issue/criterion-addressable.
4. **Evidence continuity fragility:** when BDD preflight fails, downstream evidence quality drops sharply while some reporting still appears healthy.

## Recommended alignment actions (ordered)

1. **Stabilize evidence first:** restore BDD executability in canonical contributor environments (`pip install -e .[dev]`) before status interpretation.
2. **Normalize issue lifecycle semantics:** reconcile ISSUE-0015 status/severity with its explicit “no criteria remain open” section.
3. **Increase scenario traceability density:** adopt consistent ISSUE/AC tags for stakeholder-critical scenarios across behavior files, not only selected memory scenarios.
4. **Add architecture-conformance probes to governance surface:** include at least one deterministic contract check that fails when stage-order or forbidden `U -> I` pathways are reintroduced.

## Commands used for this review

```bash
python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json
python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1
python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1
```
