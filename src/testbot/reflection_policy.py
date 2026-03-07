"""Deterministic fallback policy for answer-stage memory routing."""

from __future__ import annotations

from typing import Literal

IntentClass = Literal["memory_recall", "time_query", "non_memory"]
CapabilityStatus = Literal["ask_available", "ask_unavailable"]
FallbackAction = Literal[
    "ANSWER_TIME",
    "ANSWER_GENERAL_KNOWLEDGE",
    "ANSWER_UNKNOWN",
    "ASK_CLARIFYING_QUESTION",
    "ROUTE_TO_ASK",
    "OFFER_CAPABILITY_ALTERNATIVES",
]


def decide_fallback_action(
    *,
    intent: IntentClass,
    memory_hit: bool,
    ambiguity: bool,
    capability_status: CapabilityStatus,
    source_confidence: float | None = None,
    source_confidence_floor: float = 0.5,
) -> FallbackAction:
    """Return the fallback action for the current policy row.

    Policy intent:
    - Non-memory intents should proceed with the normal answer path.
    - Memory intents with ambiguity should disambiguate, preferring Ask when available.
    - Memory intents without an acceptable memory hit should move the user forward with alternatives.
    - Memory intents with a clean memory hit proceed with the normal answer path.
    """

    if intent == "time_query":
        return "ANSWER_TIME"

    if source_confidence is not None and source_confidence < source_confidence_floor and intent == "non_memory":
        return "ANSWER_UNKNOWN"

    if intent == "non_memory":
        return "ANSWER_GENERAL_KNOWLEDGE"

    if ambiguity:
        if capability_status == "ask_available":
            return "ROUTE_TO_ASK"
        return "ASK_CLARIFYING_QUESTION"

    if not memory_hit:
        return "OFFER_CAPABILITY_ALTERNATIVES"

    return "ANSWER_GENERAL_KNOWLEDGE"


def fallback_reason(
    *,
    intent: IntentClass,
    fallback_action: FallbackAction,
    memory_hit: bool,
    ambiguity: bool,
    source_confidence: float | None = None,
) -> str:
    """Return deterministic reason code for selected fallback branch."""

    if fallback_action == "ROUTE_TO_ASK":
        return "ambiguous_memory_candidates_with_ask_available"
    if fallback_action == "ASK_CLARIFYING_QUESTION":
        return "ambiguous_memory_candidates_without_ask"
    if fallback_action == "ANSWER_UNKNOWN":
        if intent == "non_memory" and source_confidence is not None:
            return "non_memory_low_source_confidence"
        return "insufficient_reliable_memory"
    if fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        if intent == "memory_recall" and not memory_hit and not ambiguity:
            return "memory_recall_no_confident_hit"
        return "capability_alternatives_required"
    if fallback_action == "ANSWER_TIME":
        return "time_query_direct_answer"
    return "direct_answer_path"
