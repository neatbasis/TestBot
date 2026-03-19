from __future__ import annotations

import re
from dataclasses import dataclass

from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.stabilization import StabilizedTurnState
from testbot.intent_router import IntentType, classify_intent, extract_intent_facets, validate_intent_facet_legality


_SELF_REFERENTIAL_MEMORY_PATTERNS = (
    re.compile(r"^\s*who\s+am\s+i\b", re.IGNORECASE),
    re.compile(r"^\s*what(?:\s+is|'s)\s+my\s+name\b", re.IGNORECASE),
    re.compile(r"\bremind\s+me\s+(?:what\s+)?my\s+name\s+is\b", re.IGNORECASE),
)

_TEMPORAL_FOLLOWUP_PATTERNS = (
    re.compile(r"\bwhen\s+was\s+that\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+time\s+was\s+that\b", re.IGNORECASE),
    re.compile(r"\bhow\s+long\s+ago\s+was\s+that\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ResolvedIntent:
    classified_intent: IntentType
    resolved_intent: IntentType
    rationale: str
    conflicts: tuple[str, ...] = ()


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


def _has_identity_continuity_artifacts(context: ResolvedContext) -> bool:
    return any(anchor.startswith("commit.confirmed_user_facts:") for anchor in context.history_anchors)


def _is_self_referential_memory_followup(utterance: str) -> bool:
    normalized = (utterance or "").strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in _SELF_REFERENTIAL_MEMORY_PATTERNS)


def _has_repair_offer_continuity(context: ResolvedContext) -> bool:
    return "commit.pending_repair_state:repair_offered_to_user" in context.history_anchors


def _has_memory_recall_continuity(context: ResolvedContext) -> bool:
    if context.prior_intent in {IntentType.MEMORY_RECALL, IntentType.TIME_QUERY}:
        return True
    return any(anchor.startswith("commit.confirmed_user_facts:") for anchor in context.history_anchors)


def _is_temporal_memory_followup(utterance: str) -> bool:
    normalized = (utterance or "").strip()
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in _TEMPORAL_FOLLOWUP_PATTERNS)


def resolve(*, resolution_input: IntentResolutionInput) -> ResolvedIntent:
    context = resolution_input.context
    stabilized_utterance = _stabilized_utterance_hint(resolution_input.stabilized_turn_state)
    classifier_input = stabilized_utterance or resolution_input.fallback_utterance
    classified_intent = classify_intent(classifier_input)

    tentative_resolved = classified_intent
    rationale = (
        "re-evaluated from stabilized artifact signals"
        if stabilized_utterance
        else "re-evaluated from fallback utterance metadata"
    )

    allow_continuity_override = False
    if context.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT and context.prior_intent is not None:
        tentative_resolved = context.prior_intent
        rationale = "continuity-preserving follow-up from clarification/capability flow"
        allow_continuity_override = True

    elif (
        classified_intent is IntentType.KNOWLEDGE_QUESTION
        and _has_identity_continuity_artifacts(context)
        and _is_self_referential_memory_followup(classifier_input)
    ):
        tentative_resolved = IntentType.MEMORY_RECALL
        rationale = "self-referential follow-up promoted to memory recall using committed continuity artifacts"
        allow_continuity_override = True

    elif (
        classified_intent is IntentType.KNOWLEDGE_QUESTION
        and _has_memory_recall_continuity(context)
        and _is_temporal_memory_followup(classifier_input)
    ):
        tentative_resolved = IntentType.TIME_QUERY
        rationale = "temporal follow-up promoted to time_query using memory continuity anchors"
        allow_continuity_override = True

    elif (
        classified_intent is IntentType.KNOWLEDGE_QUESTION
        and _has_repair_offer_continuity(context)
    ):
        tentative_resolved = IntentType.CAPABILITIES_HELP
        rationale = "repair-offer followup promoted to capabilities_help via committed repair anchor"
        allow_continuity_override = True

    conflicts: list[str] = []
    if classified_intent is IntentType.CONTROL and tentative_resolved is not IntentType.CONTROL:
        tentative_resolved = IntentType.CONTROL
        conflicts.append("classified_control_overrides_resolved")

    facets = extract_intent_facets(classifier_input)
    legality = validate_intent_facet_legality(tentative_resolved, facets)
    if not legality.valid and not allow_continuity_override:
        conflicts.append(f"resolved_intent_facet_conflict:{legality.reason}")
        fallback_legality = validate_intent_facet_legality(classified_intent, facets)
        tentative_resolved = classified_intent if fallback_legality.valid else IntentType.KNOWLEDGE_QUESTION
        rationale = f"{rationale}; conflict handled via legality fallback"

    return ResolvedIntent(
        classified_intent=classified_intent,
        resolved_intent=tentative_resolved,
        rationale=rationale,
        conflicts=tuple(conflicts),
    )


# Backward-compatible alias while canonical naming converges.
IntentResolution = ResolvedIntent
