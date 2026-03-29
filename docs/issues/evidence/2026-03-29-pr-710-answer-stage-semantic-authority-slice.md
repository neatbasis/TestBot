# 2026-03-29 PR-710/next answer-stage semantic authority slice

## Scope
Bounded seam reduction for assemble-stage special-answer authority.

## Findings (pre-change after #710)
- Validate-path semantics were canonicalized in #710, but `answer_assemble_for_turn_service(...)` still accepted legacy-injected special-answer constants and `build_partial_memory_clarifier`.
- Runtime-loop answer-stage wiring still pulled those assemble semantics from `sat_chatbot_memory_v2`, preserving split authority between assemble and validate.

## Canonical vs transitional authority after this slice
- **Canonical now**:
  - `testbot.answer_stage_semantics` now owns partial-memory clarifier construction policy (`build_partial_memory_clarifier`) and the assembly/validation special-answer contract values.
  - `answer_assemble_for_turn_service(...)` now consumes a canonical `AnswerStageSemanticContract` instead of per-call legacy answer constants/clarifier builder.
  - `answer_validate_for_turn_service(...)` and `stage_transitions` continue to consume the same canonical semantic contract/expectation owner from #710.
- **Still transitional/deferred**:
  - Runtime still routes telemetry/logging and some policy-core helpers via legacy façade symbols (plumbing/integration seam).

## 2026-03-29 follow-on update (post-#711 presentation seam retirement)
- `runtime_loop` now sources answer-stage presentation collaborators from canonical `testbot.application.services.answer_stage_presentation` (`ANSWER_PROMPT`, `render_context`) instead of pulling them from `sat_chatbot_memory_v2`.
- `sat_chatbot_memory_v2` keeps compatibility re-exports for `ANSWER_PROMPT` and `render_context`, but canonical presentation ownership no longer depends on legacy runtime injection in `run_chat_loop`.

## Semantic authority moved/clarified in this PR
- Moved assemble-stage clarifier wording/policy and special-answer constants from legacy per-call injection to canonical ownership in `testbot.answer_stage_semantics` via `AnswerStageSemanticContract`.
- Runtime loop is less responsible for answer-stage semantic composition because it no longer injects those semantic collaborators.
