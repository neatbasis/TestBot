from __future__ import annotations

from dataclasses import dataclass

from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.stabilization import StabilizedTurnState
from testbot.intent_router import IntentType, classify_intent


@dataclass(frozen=True)
class ResolvedIntent:
    classified_intent: IntentType
    resolved_intent: IntentType
    rationale: str


@dataclass(frozen=True)
class IntentResolutionInput:
    stabilized_turn_state: StabilizedTurnState
    context: ResolvedContext
    fallback_utterance: str = ""


def _stabilized_utterance_hint(stabilized_turn_state: StabilizedTurnState) -> str:
    for fact in stabilized_turn_state.candidate_facts:
        if fact.key != "utterance_raw":
            continue
        if fact.value.strip():
            return fact.value
    return ""


def resolve(*, resolution_input: IntentResolutionInput) -> ResolvedIntent:
    context = resolution_input.context
    stabilized_utterance = _stabilized_utterance_hint(resolution_input.stabilized_turn_state)
    classifier_input = stabilized_utterance or resolution_input.fallback_utterance
    classified_intent = classify_intent(classifier_input)
    if context.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT and context.prior_intent is not None:
        return ResolvedIntent(
            classified_intent=classified_intent,
            resolved_intent=context.prior_intent,
            rationale="continuity-preserving follow-up from clarification/capability flow",
        )
    return ResolvedIntent(
        classified_intent=classified_intent,
        resolved_intent=classified_intent,
        rationale=(
            "re-evaluated from stabilized artifact signals"
            if stabilized_utterance
            else "re-evaluated from fallback utterance metadata"
        ),
    )


# Backward-compatible alias while canonical naming converges.
IntentResolution = ResolvedIntent
