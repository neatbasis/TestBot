# ISSUE-0022 — stage rerank compatibility-wrapper retirement execution

## Change type

- [x] Wrapper retirement row
- [ ] Compatibility retirement row
- [ ] Retirement readiness evidence-only PR

## Issue link

Issue: ISSUE-0022

## Selected retirement row

- **Selected row:** retire compatibility wrapper `_stage_rerank_for_turn_service`.
- **Why this row now (leverage consumed):** PR #690 already established caller-census + runtime-equivalence/control-point leverage, and PR #691 made retirement evidence structure canonical; this PR consumes that leverage on latest `main` instead of reopening scorer redesign scope.
- **Bounded authority slice in scope:** only rerank stage wiring authority in `sat_chatbot_memory_v2` compatibility hooks.

## Current authority map

- **Current owner/path:** rerank semantics are owned by `stage_rerank(...)` and consumed through `context_retrieval_runtime_service.stage_rerank_for_turn_service(...)`.
- **Canonical runtime/control-point path:** runtime loop path and turn-pipeline hook both route through `context_retrieval_runtime_service.stage_rerank_for_turn_service(...)`.
- **Compatibility delegation posture (if any):** wrapper function was only a forwarding seam from hook wiring to runtime service.

## Ideal future state

- **Target owner/path after retirement:** direct hook wiring to `context_retrieval_runtime_service.stage_rerank_for_turn_service(...)` with explicit `stage_rerank_fn=stage_rerank`.
- **What canonical path should no longer depend on:** `_stage_rerank_for_turn_service` wrapper symbol and wrapper-specific tests.
- **Outside scope in this PR:** scorer internals/policy redesign, threshold redesign, confidence payload redesign, broader retrieval restructuring.

## Retirement-specific evidence requirements

### Caller census

- Evidence (in-repo callers + any known external compatibility callers):
  - refreshed source-tree census before removal showed wrapper only in definition + hook assignment (same as #690);
  - after removal, source-tree census confirms zero wrapper symbol references.
- Claim supported by this evidence and why:
  - Evidence X supports claim Y because Z: source-tree census supports “wrapper is compatibility-only and removable in-repo” because the only in-repo callsite was legacy hook wiring.
- Stronger claim not yet supported and why not:
  - It does not yet support stronger claim W because Q: this does not prove there are zero out-of-repo consumers importing private helper names from historical versions.

### Semantic ownership census

- Evidence (who currently owns behavior semantics vs forwarding mechanics):
  - `stage_rerank(...)` remains semantic owner for rerank behavior; runtime service adapter remains canonical control-point owner for pipeline contract normalization.
- Claim supported by this evidence and why:
  - Evidence X supports claim Y because Z: ownership census supports “retirement removes forwarding mechanics only” because semantic decision logic is unchanged and still lives in existing owner functions.
- Stronger claim not yet supported and why not:
  - It does not yet support stronger claim W because Q: this PR does not retire broader rerank category debt (scorer internals/policy decomposition).

### Removal criteria checklist

- [x] Canonical runtime path ownership is explicit for the behavior being retired.
- [x] Compatibility delegation is explicitly bounded.
- [x] Caller census supports retirement posture claimed.
- [x] Anti-backslide guard exists (test/assertion/checklist) for the retired surface.
- [x] Deferred category debt (if any) is explicitly named.

### Runtime equivalence or control-point proof

- Evidence (equivalence test, invariant check, or control-point assertions):
  - runtime-equivalence test for `stage_rerank_for_turn_service(...)` vs direct stage-contract execution remains passing;
  - runtime wiring tests still assert direct runtime-service control point.
- Claim supported by this evidence and why:
  - Evidence X supports claim Y because Z: equivalence/control-point tests support “behavior preserved under direct wiring” because the retired symbol only forwarded to the same canonical service call.
- Stronger claim not yet supported and why not:
  - It does not yet support stronger claim W because Q: these checks do not prove category-level optimality of scorer architecture; they only prove this bounded retirement row.

### Explicit retirement-finishability statement

- **Is retirement directly finishable now?** Yes, on latest `main`.
- **If no, what specifically blocks retirement?** N/A.
- **What smallest change/evidence would make retirement directly finishable?** N/A; this PR executes direct removal.

## Implemented change

- **What was changed in this PR:**
  - removed `_stage_rerank_for_turn_service` from `sat_chatbot_memory_v2.py`;
  - replaced hook wiring with direct lambda delegation to `context_retrieval_runtime_service.stage_rerank_for_turn_service(...)`;
  - replaced wrapper-census tests with retirement anti-backslide assertions (no wrapper symbol, direct service wiring).
- **Why this is a bounded retirement move (not broader redesign):** no rerank decision/scorer semantics changed; only compatibility seam removal + guard updates.

## Strongest justified claim

- **Strongest bounded claim this PR justifies:** the staged rerank wrapper-retirement row program is complete in-repo, with canonical runtime control-point behavior preserved and scorer-category redesign explicitly out of scope.

## Remaining deferred scope

### Rows remaining

- None for the staged rerank wrapper-retirement row program.

### Category debt remaining

- Scorer internals/category decomposition and related policy-shaping design debt.

## Options opened by this PR

For each option include:
- **What the option would do:** produce scorer-category debt decomposition and select smallest bounded scorer-contract/scorer-execution slice.
  - **What it depends on:** explicit category inventory, bounded slice selection criteria, and control-point invariants for that slice.
  - **Recommended next option and why:** recommended, because wrapper-row leverage is now consumed and the next unit of progress is category-level decomposition.
- **What the option would do:** perform broad scorer redesign immediately.
  - **What it depends on:** substantial design + validation surface in one step.
  - **Recommended next option and why:** not recommended immediately; weaker boundedness and higher blast radius than decomposition-first sequencing.

## How this PR makes later moves easier

- **Ambiguity reduced:** wrapper retirement no longer blocks authority-map reads for rerank control point.
- **Ownership boundary made clearer:** runtime hook now directly names canonical service owner and semantic stage hook.
- **What future move is now safer/smaller/faster:** scorer-category decomposition can proceed without wrapper-retirement ambiguity.

## Operational posture (lightweight)

- **Risk level (low / medium / high):** low.
- **Rollback posture:** restore removed wrapper and rebind hook if regression discovered.
- **What to watch after merge:** runtime pipeline rerank stage behavior and compatibility import expectations.

## PR-ready summary

- **Selected retirement row processed:** stage rerank wrapper retirement.
- **Leverage consumed:** #690 caller-census + runtime-equivalence leverage, using #691 retirement template contract.
- **Bounded authority moved (or readiness evidence hardened):** removed compatibility wrapper seam; direct canonical control-point wiring retained.
- **Rows remaining + category debt remaining:** no rerank wrapper rows remain; scorer-category debt remains deferred.
- **Recommended next move:** start scorer-category debt decomposition with smallest bounded scorer-contract/scorer-execution slice.

## Tests run

- `python -m pytest tests/test_context_retrieval_runtime.py -k "stage_rerank_for_turn_service_runtime_path_is_equivalent_to_direct_stage_contract or stage_rerank_wrapper_is_retired_in_src_tree_runtime_wiring"`
- `python -m pytest tests/test_context_retrieval_runtime_compat_wrappers.py -k "stage_rerank_for_turn_service_wrapper_is_retired"`
- `python -m pytest tests/test_runtime_modes.py -k "runtime_hooks_resolve_context_retrieval_control_point_at_runtime or canonical_stage_rerank_path_consumes_runtime_decision_policy_assembly"`
- `python scripts/all_green_gate.py` *(fails on pre-existing behave scenarios unrelated to this row; see gate output for listed failing scenarios).*
