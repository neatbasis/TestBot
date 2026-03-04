"""Deterministic fallback policy for answer-stage memory routing."""

from __future__ import annotations

from typing import Literal

IntentClass = Literal["memory_recall", "non_memory"]
CapabilityStatus = Literal["ask_available", "ask_unavailable"]
FallbackAction = Literal[
    "ANSWER_GENERAL_KNOWLEDGE",
    "ASK_CLARIFYING_QUESTION",
    "ROUTE_TO_ASK",
    "EXACT_MEMORY_FALLBACK",
]


def decide_fallback_action(
    *,
    intent: IntentClass,
    memory_hit: bool,
    ambiguity: bool,
    capability_status: CapabilityStatus,
) -> FallbackAction:
    """Return the exact fallback action for the current policy row.

    Policy intent:
    - Non-memory intents should proceed with the normal answer path.
    - Memory intents with ambiguity should disambiguate, preferring Ask when available.
    - Memory intents without an acceptable memory hit must emit exact memory fallback.
    - Memory intents with a clean memory hit proceed with the normal answer path.
    """

    if intent == "non_memory":
        return "ANSWER_GENERAL_KNOWLEDGE"

    if ambiguity:
        if capability_status == "ask_available":
            return "ROUTE_TO_ASK"
        return "ASK_CLARIFYING_QUESTION"

    if not memory_hit:
        return "EXACT_MEMORY_FALLBACK"

    return "ANSWER_GENERAL_KNOWLEDGE"
