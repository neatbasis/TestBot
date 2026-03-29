# PR #690 wrapper-retirement finishability evidence (ISSUE-0022)

- **Date:** 2026-03-29
- **Related Issue:** ISSUE-0022
- **Scope:** process the remaining rerank row (wrapper retirement) by reducing uncertainty with caller census + control-point/runtime-equivalence evidence, while keeping scorer-internals category debt explicit.

## 1) Selected row

- **Row processed:** residual rerank row — wrapper retirement finishability.
- **Why this row now:** after #689, invocation policy, threshold/profile policy, and confidence-decision projection were already runtime-owned. The highest leverage-to-scope move is to reduce uncertainty on whether wrapper retirement is directly finishable.

## 2) Current authority map

- **Current owner/path:** rerank semantics are runtime-owned through `context_retrieval_runtime` helpers; scorer execution internals remain compatibility-owned in monolith `stage_rerank(...)`.
- **Runtime/control-point path:** `entrypoints/runtime_loop.py` binds rerank hook through `context_retrieval_runtime_service.stage_rerank_for_turn_service(...)`.
- **Compatibility posture:** `_stage_rerank_for_turn_service` still exists in `sat_chatbot_memory_v2.py` for legacy runtime path wiring.
- **Smallest coherent authority slice in this PR:** caller census + runtime-equivalence/control-point evidence for wrapper-retirement finishability (no scorer-internals move).

## 3) Ideal future state

- **Ultimate authority location:** canonical runtime path sources rerank entirely via runtime-owned seam service without compatibility wrapper dependency.
- **Canonical path should no longer source from legacy ownership:** `_stage_rerank_for_turn_service` should not be required for canonical runtime execution.
- **Outside scope:** scorer execution internals and their possible adapter/port extraction remain deferred category debt.

## 4) Implemented change

- Added deterministic runtime-equivalence test asserting `stage_rerank_for_turn_service(...)` produces results equivalent to direct stage-contract execution over normalized `docs_and_scores` inputs.
- Added executable caller-census test asserting `_stage_rerank_for_turn_service` has only two source-tree occurrences: its definition and compatibility-only legacy wiring assignment.
- Why bounded/coherent: both tests target wrapper-retirement decision evidence only; no policy movement and no scorer-internals mutation.

## 5) Evidence

### Grounded behavior

- Runtime-equivalence test proves service-layer rerank wrapper preserves direct stage contract semantics (state + ordered rerank hit identity projection).

### Compatibility delegation

- Caller-census test proves `_stage_rerank_for_turn_service` is confined to compatibility posture in source tree (definition + legacy pipeline assignment only).

### Ownership / anti-backslide posture

- Executable census prevents silent expansion of wrapper call-surface ownership in production source tree.

### Runtime control-point evidence

- Existing runtime-loop tests plus new service-level equivalence proof strengthen that canonical runtime path control point remains runtime-service-owned and behavior-preserving.

## 6) Strongest justified claim

After this PR, wrapper-retirement finishability is better constrained: canonical runtime rerank control-point behavior is proven equivalent at the service seam, and source-tree caller census shows wrapper usage is compatibility-only in production code.

## 7) Remaining deferred scope

### Rows remaining

- Wrapper retirement execution/removal PR itself (decision now better informed but not performed in this PR).

### Category debt remaining

- Scorer internals (execution contract posture, scorer implementation boundary/adapter decision).

## 8) Finishability assessment

- **Is next remaining row directly finishable?** Potentially yes, pending final retirement PR choice and compatibility/deprecation handling.
- **Current blocker (if any):** confirming external compatibility expectations and selecting retirement mode (immediate removal vs temporary bridge with explicit expiry).
- **What removes block:** explicit retirement PR with deprecation/removal handling and rerank-path invariance checks after removal.

## 9) Options opened by this PR

1. **Retire wrapper now**
   - Do: remove `_stage_rerank_for_turn_service` and legacy assignment path usage.
   - Depends on: compatibility acceptance for removal.
   - Recommended when: compatibility obligations are satisfied/closed.
2. **Keep wrapper temporarily with stricter checks**
   - Do: retain wrapper but enforce tighter anti-backslide checks and explicit expiry criteria.
   - Depends on: choosing explicit deprecation window.
   - Not preferred long-term: preserves temporary surface.
3. **Add scorer execution adapter/port first**
   - Do: introduce minimal scorer execution boundary before wrapper retirement.
   - Depends on: deciding scorer-internals split now vs later.
   - Recommended only if retirement uncovers execution-contract coupling risk.

## 10) How this PR makes later moves easier

- **Ambiguity reduced:** wrapper usage in production source is now executable-censused.
- **Ownership boundary clearer:** runtime seam equivalence is explicit at rerank stage-service boundary.
- **Future move safer/smaller/faster:** wrapper-retirement PR can focus on removal mechanics and compatibility handling, not first-time behavior discovery.

## 11) PR-ready summary

- **Row processed:** wrapper-retirement finishability evidence.
- **Leverage consumed:** post-#689 runtime seam ownership and existing control-point routing.
- **Bounded authority moved:** none (evidence-only PR); ownership proof strengthened through tests.
- **Deferred remains:** wrapper removal execution decision + scorer-internals category debt.
- **Recommended next move:** perform wrapper retirement PR if compatibility obligations allow; otherwise add smallest scorer execution contract and keep wrapper temporary with explicit expiry.

## 12) Tests run

- `python -m pytest tests/test_context_retrieval_runtime.py -k "stage_rerank_for_turn_service_runtime_path_is_equivalent_to_direct_stage_contract or stage_rerank_wrapper_caller_census_is_compatibility_only_in_src_tree"`
- `python -m pytest tests/test_runtime_modes.py -k "runtime_loop_binds_migrated_context_retrieval_hook_surfaces_via_canonical_service or runtime_loop_context_retrieval_residual_monolith_touchpoints_are_explicit_policy_core_only"`

## Additional retirement-row requirements

### Caller census

- Executable source-tree census added (`_stage_rerank_for_turn_service` appears only in definition + legacy wiring assignment).

### Semantic ownership census

- Canonical rerank policy/decision shaping ownership remains runtime-owned in `context_retrieval_runtime` helpers; wrapper remains forwarding posture.

### Removal criteria checklist

- Canonical runtime helper ownership for invocation policy / threshold profile / confidence projection: already true from prior PRs.
- Caller census for wrapper necessity: now executable evidence in this PR.
- Runtime equivalence/control-point proof: strengthened in this PR.
- Retirement directly finishable now: **decision-ready but not executed in this PR**.

### Runtime equivalence or control-point proof

- Added deterministic rerank service equivalence test.

### Explicit retirement-finishability statement

- Retirement is now **better bounded and plausibly directly finishable**, but final removal action remains a follow-up change because this PR is evidence-hardening only.
