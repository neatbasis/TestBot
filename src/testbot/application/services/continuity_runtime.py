"""Canonical runtime continuity/unresolved-intent policy helpers.

Ownership:
- This module is the canonical owner for runtime-loop continuity semantics
  deciding whether unresolved intent carries into the next turn.
- Compatibility layers may delegate here during legacy retirement.
"""

from __future__ import annotations

from dataclasses import replace

from testbot.answer_contract_constants import CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER
from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service
from testbot.pipeline_state import PipelineState


def is_capabilities_help_answer(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith("runtime mode:") and "memory recall:" in normalized and "home assistant" in normalized


def should_preserve_unresolved_intent(*, final_answer: str) -> bool:
    normalized = (final_answer or "").strip()
    if not normalized:
        return False
    return answer_stage_runtime_service.is_clarification_answer(
        normalized,
        clarify_answer=CLARIFY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
    ) or is_capabilities_help_answer(normalized)


def apply_unresolved_intent_carryover(state: PipelineState) -> PipelineState:
    unresolved_intent = state.resolved_intent if should_preserve_unresolved_intent(final_answer=state.final_answer) else ""
    return replace(state, prior_unresolved_intent=unresolved_intent)


__all__ = [
    "apply_unresolved_intent_carryover",
    "is_capabilities_help_answer",
    "should_preserve_unresolved_intent",
]
