# Memory recall root-cause review: feedback relevance, accuracy, and application map (2026-03-06)

## Purpose
This follow-up review assesses how relevant and accurate the external feedback is relative to the existing root-cause report in `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`, and identifies where in this repository the feedback should be applied.

## Executive assessment
The feedback is **highly relevant** and **mostly accurate** for this codebase. Its central claim—evaluate memory recall maturity as preserved invariants under allowed transformations rather than fixture-only string correctness—matches observed implementation and documentation gaps.

Current fit summary:
- **Strongly aligned:** runtime-parity concern (RC-5), temporal transformation weakness (RC-3), narrow ambiguity modeling (RC-4), and confidence boundary behavior (RC-2).
- **Partially aligned with caveat:** RC-1 policy/contract gap is real, but the repository currently has **internal contract drift** between directive docs and canonical invariants docs, so this is broader than a single product expectation mismatch.

## Feedback claim-by-claim validation against repository

### 1) “Maturity should be measured as invariants under transformations”
**Assessment:** Accurate and directly applicable.

Evidence in repo:
- `features/memory_recall.feature` and `features/steps/memory_steps.py` use deterministic fixture harness behavior; this validates contract shape but under-exercises transformation robustness.
- `src/testbot/rerank.py` exposes objective components, near-tie detection, and confidence decisions that are suitable invariant signals.
- Existing invariant docs focus mostly on response contract behavior and fallback modes; they do not define metamorphic transformation families explicitly.

### 2) RC-1 as policy/contract gap
**Assessment:** Accurate, and currently wider than stated because docs are inconsistent.

Evidence in repo:
- Runtime policy in `src/testbot/reflection_policy.py` routes non-hit memory cases to `OFFER_CAPABILITY_ALTERNATIVES` and only routes to strict unknown under low source-confidence condition.
- `docs/invariants.md` defines INV-002 as **progressive fallback**.
- `docs/directives/invariants.md` still defines INV-002 as **exact fallback**; this conflicts with runtime and BDD feature wording.

Implication:
- Stakeholder confusion is not only expectation-vs-policy; there is canonical-document split that can mislead implementation and review.

### 3) RC-2 as decision-boundary/confidence separation gap
**Assessment:** Accurate.

Evidence in repo:
- `src/testbot/rerank.py` default thresholds include `min_margin_to_second = 0.0` and `allow_ambiguity_override = False`.
- `has_sufficient_context_confidence_from_objective(...)` allows confidence when top score passes minimum and ambiguity does not trigger, even if margin is tiny.

Implication:
- Feedback’s monotonic-confidence framing is relevant for robust calibration.

### 4) RC-3 as semantic-time transformation gap
**Assessment:** Accurate.

Evidence in repo:
- `src/testbot/time_parse.py::parse_target_time` returns `now` when broad phrasing is not explicitly matched.
- Broad temporal paraphrases (e.g., “earlier this week”) are not directly represented; this can collapse intended temporal semantics.

### 5) RC-4 as ambiguity-region modeling gap
**Assessment:** Accurate.

Evidence in repo:
- `src/testbot/rerank.py` sets ambiguity unresolved only when near-tie candidates share identical tie-break key values.
- Slight differences in tie-break attributes can suppress ambiguity despite practical uncertainty.

### 6) RC-5 as runtime-parity gap
**Assessment:** Accurate and already recognized by existing issue governance.

Evidence in repo:
- `features/steps/memory_steps.py` builds synthetic state and sets `context_confident = bool(candidates)` rather than invoking runtime rerank/confidence pipeline.
- `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` documents parity risk and calls for deterministic parity regression checks.

## Relevance matrix: where this feedback should be applied

### Documentation surfaces
1. `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
   - Add a maturity framing section (transformations, invariants, parity) so findings are framed as enforceable invariants, not only branch behavior.
2. `docs/invariants.md`
   - Extend registry with memory-recall transformation invariants (paraphrase stability, temporal normalization consistency, confidence/ambiguity monotonicity, runtime-parity).
3. `docs/directives/invariants.md`
   - Reconcile INV-002 with `docs/invariants.md` and runtime fallback policy to remove contradictory guidance.
4. `docs/testing.md`
   - Add required metamorphic and runtime-parity checks as explicit QA gates.
5. `docs/qa/smoke-evidence-contract.md`
   - Add a memory-recall evidence artifact contract for maturity/parity outputs.

### Runtime and evaluation code surfaces
1. `src/testbot/time_parse.py`
   - Expand temporal phrase normalization coverage for broad natural language variants.
2. `src/testbot/rerank.py`
   - Introduce/validate stronger confidence separation constraints and broader ambiguity-region handling.
3. `features/steps/memory_steps.py` (and possibly additional step modules)
   - Add a runtime-parity execution path that reuses actual rerank/confidence functions for at least one BDD family.
4. `scripts/eval_recall.py` + parity tests in `tests/test_eval_runtime_parity.py`
   - Add metamorphic relation checks and machine-readable invariant pass-rate outputs.

## Priority and sequencing assessment
The suggested sequencing from the feedback is directionally correct; this repository should prioritize:
1. **Runtime parity first** (close representation/runtime split).
2. **Contract reconciliation second** (single canonical fallback and maturity contract).
3. **Confidence + ambiguity boundary hardening third**.
4. **Temporal transformation expansion fourth**.

This sequence best reduces false confidence from green surrogate tests.

## Actionable gaps to open/track

### Gap A — Canonical invariant contract drift across docs
`docs/invariants.md` and `docs/directives/invariants.md` disagree on INV-002 behavior, which undermines RC-1 closure and stakeholder alignment.

:::task-stub{title="Unify INV-002 fallback contract across canonical and directive docs"}
Update `docs/directives/invariants.md` so INV-002 matches the progressive fallback contract in `docs/invariants.md` and runtime policy in `src/testbot/reflection_policy.py`.

Then add an explicit “source of truth” note in both files that `docs/invariants.md` is canonical and directive mirrors must stay synchronized.

Add a short changelog note in `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` documenting the contract reconciliation decision and rationale.
:::

### Gap B — No explicit metamorphic invariant registry for memory recall
Current invariants are contract-oriented but do not enumerate transformation families and expected stable relations.

:::task-stub{title="Add memory-recall metamorphic invariants and maturity gates to QA docs"}
Create a new section in `docs/invariants.md` titled “Memory recall metamorphic invariants” with at least these invariants: paraphrase stability, temporal normalization consistency, confidence monotonicity, ambiguity monotonicity, and runtime-parity class consistency.

For each invariant, define: transformation family, measurable signal, pass criterion, and intended failure interpretation.

Reflect these checks in `docs/testing.md` with deterministic commands and expected artifact locations.
:::

### Gap C — BDD harness does not prove runtime parity for memory decisions
Synthetic BDD state construction in `features/steps/memory_steps.py` bypasses runtime confidence/ambiguity logic.

:::task-stub{title="Add runtime-parity memory recall BDD path using real rerank/confidence logic"}
In `features/steps/memory_steps.py`, add a new step path that invokes the same rerank/confidence functions used by runtime (`testbot.rerank` and related parsing modules) rather than synthetic `context_confident = bool(candidates)`.

Add one scenario in `features/memory_recall.feature` that compares deterministic harness outcome class to runtime-parity outcome class for the same fixture family.

Ensure assertions include intermediate signals (`scored_candidates`, `near_tie_candidates`, `ambiguity_detected`) so parity drift is visible before final answer drift.
:::

### Gap D — Confidence boundary is permissive for near ties
Current thresholds allow tiny top-vs-second margins to pass confidence when ambiguity is not triggered.

:::task-stub{title="Introduce measurable confidence-margin calibration for memory recall decisions"}
In `src/testbot/rerank.py`, define a non-zero default for `min_margin_to_second` (or load from config) and add test coverage in `tests/test_rerank.py` for boundary cases where tiny margins should fail confidence.

Document the calibration rationale and target ranges in a QA doc section (either `docs/testing.md` or a new `docs/qa/memory-recall-maturity-model.md`) so threshold updates are traceable.

Add parity regression cases to `tests/test_eval_runtime_parity.py` that verify confidence class behavior at the margin boundary.
:::

### Gap E — Temporal broad-phrase handling is incomplete
Unrecognized broad temporal expressions default to `now`, weakening intended temporal semantics.

:::task-stub{title="Expand and verify temporal phrase normalization coverage for memory recall"}
Extend `src/testbot/time_parse.py::parse_target_time` to recognize broad phrases such as “earlier this week”, “this morning”, and “recently” with deterministic mappings.

Add directed tests in `tests/test_time_parse.py` and/or `tests/test_time_parse_directional.py` that validate equivalent phrase families map to comparable target windows.

Add fixture families in parity/eval tests (`tests/test_eval_runtime_parity.py` and related fixture JSONL files) to ensure ranking behavior remains stable under temporal paraphrase transformations.
:::


## Decision record (2026-03-06): INV-002 fallback contract normalization
- **Decision:** Keep the progressive fallback contract as canonical for INV-002 across `docs/invariants.md`, `docs/directives/invariants.md`, `docs/testing.md`, and `docs/quickstart.md`.
- **Contract:** For insufficient memory, require either one targeted clarifier or at least two capability-based alternatives; for partial/ambiguous memory, require a brief summary plus one bridging clarifier; reserve exact `I don't know from memory.` for explicit deny/safety-only cases.
- **Rationale:** This matches runtime routing in `src/testbot/reflection_policy.py` and existing BDD wording for progressive assist/ambiguity scenarios, removing contradictory exact-string fallback guidance from docs and checklists.

## Proposed evidence artifact additions
To make this feedback operational, add two artifacts in future QA runs:
- `memory-maturity-summary.json`: contract version, runtime version, invariant pass rates, metamorphic pass rates, runtime-vs-BDD parity score, assessed maturity level.
- `memory-maturity-details.jsonl`: one record per transformation family/test case with intermediate signals and pass/fail reasons.

## Final relevance/accuracy conclusion
The feedback is **relevant and technically sound for this repository**. It should be applied as a maturity-contract extension across docs, test strategy, and parity execution paths—not as a wording-only fallback tweak.
