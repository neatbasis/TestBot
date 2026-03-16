# Coordination-failure contract drift matrix (PRs #481–#489)

## Why this series was vulnerable before code-level review

The workstream was vulnerable to coordination failure because the requested tasks were semantically coupled but executed as independent PR slices. In practice, the PR chain evolved one governance subsystem in parts (rules, schema, derivations, gate behavior, evidence references, and routing) rather than implementing a frozen target contract first.

This creates a predictable drift pattern:

1. **Contract written implicitly across merges** rather than explicitly once.
2. **Hidden sequencing dependencies** between PRs touching shared control surfaces.
3. **Duplicate intent risks** when similarly scoped changes are queued independently.

## Canonical capability map

The table below turns the high-level concern into a concrete drift matrix so reviewers can reason about coupling and dependency order.

| Capability / contract surface | #481 | #482 | #483 | #484 | #485 | #486 | #487 | #488 | #489 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shared governance validator primitives/rulesets | **Implements** baseline shared rule surfaces | Depends on profile-facing rule reuse | Depends on rule semantics | Depends on rule semantics | Depends on linkage rule semantics | Depends on rule categories for skip logic | Depends on reference rule semantics | Depends on same reference rule semantics | Depends on gate output semantics rooted in these rules |
| Issue schema + state model validity | References pre-existing model | Depends on issue validator outcomes | **Implements/redefines** issue schema/state transitions | Depends on issue metadata shape for escalation derivation | Depends on explicit issue-ID linkage semantics | Depends indirectly via gate skip behavior on issue checks | **Extends** accepted references via manifest links | **Potentially redefines/duplicates** manifest-linked references | Consumes outputs from prior issue/gate validity decisions |
| RED_TAG derivation from issue metadata | Not primary | Not primary | Provides metadata semantics consumed downstream | **Implements/redefines** RED_TAG generation behavior | Depends on explicit issue linkage for completeness | Depends on whether RED_TAG checks can be skipped | May add evidence references that RED_TAG validators ingest | May duplicate/refine same evidence paths | Consumes escalations as triage inputs |
| Gate profile model (`all_green_gate.py`) | Supplies reusable governance checks | **Implements** triage/readiness profile layer | Depends on validator semantics | Depends on RED_TAG checks in profiles | Depends on linkage checks in profiles | **Redefines execution surface** via changed-path skip policy | Depends on profile inclusion of manifest checks | Depends on same surface (duplicate scope risk) | **Depends on/extends** gate outputs for routing |
| Changed-path-aware governance skipping | Not primary | Creates profile context later used here | Depends on what issue paths imply schema checks | Depends on RED_TAG path assumptions | Depends on linkage file/path assumptions | **Implements/redefines** skip policy | Depends on whether manifests trigger checks | Depends on same trigger semantics | Consumes resulting pass/fail/skip outputs |
| Explicit feature/status + issue linkage | Baseline shared semantics | Depends on linkage checks presence in profile | Depends on issue schema identifiers | Indirect | **Implements** explicit linkage contract | Depends on path logic around linkage files | Extends linkage graph to include manifests | Duplicate/superseding extension risk | Consumes linkage-rich outputs for routing decisions |
| Evidence manifest format + validator support | Baseline validators may expose hook points | Depends on profile wiring | Depends on schema/reference acceptance | May consume manifest-backed evidence in escalation context | Depends on linkage validator extension points | Depends on changed-path detection for manifest files | **Implements** manifest generation + validator support | **Likely duplicates/supersedes same intent** | Consumes manifest-aware gate outcomes |
| Triage routing from gate/readiness outputs | Not primary | Produces profile outputs consumed by router | Depends on issue-state semantics for routing interpretation | Depends on escalation semantics | Depends on explicit linkage quality | Depends on skip behavior correctness | Depends on manifest-backed evidence availability | Depends on deduplicated manifest semantics | **Implements** post-gate routing behavior |

## Observed coordination risk classes

- **Semantic coupling with split ownership**: multiple PRs edited effectively the same contract boundary.
- **Order-sensitive merges**: several later PRs assume semantics established in earlier PRs, but those assumptions are not encoded as explicit dependency metadata.
- **Duplicate-intent merge risk**: near-identical intent in separate PRs creates supersession ambiguity unless one canonical owner reconciles before merge.

## Canonical freeze reference

Temporary contract freeze and canonical precedence for the affected control surfaces are captured in: `docs/issues/governance-control-surface-contract-freeze.md`.

## Recommended sequencing model for future governance refactors

Use this sequence as the default for similar work:

1. Define and review a single **target canonical contract** document for governance + evidence + triage.
2. Land shared governance primitives.
3. Land issue schema/state model updates.
4. Land RED_TAG derivation from canonical issue records.
5. Land gate profile model.
6. Land changed-path gate policy.
7. Land explicit feature-status/issue linkage.
8. Land evidence manifest format and validators.
9. Land triage router consuming stabilized gate outputs.

## Guardrails to prevent repeat coordination failures

- Require PR dependency declarations when touching any of:
  - `scripts/all_green_gate.py`
  - `scripts/validate_issue_links.py`
  - `scripts/validate_issues.py`
  - `docs/issues.md`
- Disallow concurrent non-stacked PRs that modify the above control surfaces.
- Require each PR to include a short **contract delta** section:
  - What canonical behavior it implements.
  - What prior PR contract version it depends on.
  - Which invariants must remain unchanged.

