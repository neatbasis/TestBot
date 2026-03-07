from __future__ import annotations

from dataclasses import dataclass

from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.intent_router import IntentType, classify_intent


@dataclass(frozen=True)
class IntentResolution:
    classified_intent: IntentType
    resolved_intent: IntentType
    rationale: str


def resolve(*, utterance: str, context: ResolvedContext) -> IntentResolution:
    classified_intent = classify_intent(utterance)
    if context.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT and context.prior_intent is not None:
        return IntentResolution(
            classified_intent=classified_intent,
            resolved_intent=context.prior_intent,
            rationale="continuity-preserving follow-up from clarification/capability flow",
        )
    return IntentResolution(
        classified_intent=classified_intent,
        resolved_intent=classified_intent,
        rationale="re-evaluated from current utterance",
    )
