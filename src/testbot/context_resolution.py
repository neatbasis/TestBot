from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from testbot.answer_contract_constants import CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER
from testbot.continuity_read_model import (
    ContinuityReadModel,
    continuity_context_anchors,
    continuity_prior_intent_hint,
    continuity_read_model_from_pipeline_state,
)
from testbot.intent_router import IntentType
from testbot.pipeline_state import PipelineState


class ContinuityPosture(StrEnum):
    PRESERVE_PRIOR_INTENT = "preserve_prior_intent"
    REEVALUATE = "reevaluate"


@dataclass(frozen=True)
class ResolvedContext:
    history_anchors: tuple[str, ...]
    ambiguity_flags: tuple[str, ...]
    continuity_posture: ContinuityPosture
    prior_intent: IntentType | None


def _is_short_affirmation(user_input: str) -> bool:
    normalized = (user_input or "").strip().lower().rstrip(".!?")
    return normalized in {"yes", "yeah", "yep", "yup", "ok", "okay", "sure", "please", "yes please", "ok please", "okay please"}


def _is_clarification_or_capability_confirmation_answer(text: str) -> bool:
    # Import lazily to avoid package-init import cycles in domain bootstrap paths.
    from testbot.application.services.answer_response_type_classifier import (
        is_clarification_or_capability_confirmation_answer,
    )

    return is_clarification_or_capability_confirmation_answer(
        text,
        clarify_answer=CLARIFY_ANSWER,
        route_to_ask_answer=ROUTE_TO_ASK_ANSWER,
    )


def _parse_prior_intent(
    prior_pipeline_state: PipelineState | None,
    *,
    prior_continuity: ContinuityReadModel | None = None,
) -> IntentType | None:
    continuity = prior_continuity or continuity_read_model_from_pipeline_state(prior_pipeline_state)
    prior_intent_raw = continuity_prior_intent_hint(continuity).strip()
    if not prior_intent_raw:
        return None
    try:
        return IntentType(prior_intent_raw)
    except ValueError:
        return None


def _commit_continuity_anchors(
    prior_pipeline_state: PipelineState | None,
    *,
    prior_continuity: ContinuityReadModel | None = None,
) -> tuple[str, ...]:
    continuity = prior_continuity or continuity_read_model_from_pipeline_state(prior_pipeline_state)
    return continuity_context_anchors(continuity)


def resolve(
    *,
    utterance: str,
    prior_pipeline_state: PipelineState | None,
    prior_continuity: ContinuityReadModel | None = None,
) -> ResolvedContext:
    prior_intent = _parse_prior_intent(prior_pipeline_state, prior_continuity=prior_continuity)
    anchors: list[str] = []
    flags: list[str] = []

    if prior_intent is not None:
        anchors.append(f"prior_intent:{prior_intent.value}")

    anchors.extend(_commit_continuity_anchors(prior_pipeline_state, prior_continuity=prior_continuity))

    if _is_short_affirmation(utterance):
        flags.append("short_affirmation")

    continuity_posture = ContinuityPosture.REEVALUATE
    prior_answer = (prior_pipeline_state.final_answer if prior_pipeline_state else "") or ""
    if prior_intent is not None and _is_short_affirmation(utterance) and _is_clarification_or_capability_confirmation_answer(prior_answer):
        continuity_posture = ContinuityPosture.PRESERVE_PRIOR_INTENT
        anchors.append("clarification_continuity")

    return ResolvedContext(
        history_anchors=tuple(anchors),
        ambiguity_flags=tuple(flags),
        continuity_posture=continuity_posture,
        prior_intent=prior_intent,
    )
