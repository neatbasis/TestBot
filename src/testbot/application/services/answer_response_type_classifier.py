"""Canonical answer response-type classification helpers.

Ownership:
- This module owns canonical answer response-type predicates reused across
  answer-stage, continuity, and context-resolution services.
"""

from __future__ import annotations


def is_clarification_answer(
    text: str,
    *,
    clarify_answer: str,
    route_to_ask_answer: str,
) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    return (
        normalized in {clarify_answer, route_to_ask_answer}
        or lowered.startswith("can you clarify")
        or lowered.startswith("i can disambiguate this with a quick follow-up question")
        or lowered.startswith("i found related memory fragments (")
    )


def is_capabilities_help_answer(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith("runtime mode:") and "memory recall:" in normalized and "home assistant" in normalized


def is_clarification_or_capability_confirmation_answer(
    text: str,
    *,
    clarify_answer: str,
    route_to_ask_answer: str,
) -> bool:
    return is_clarification_answer(
        text,
        clarify_answer=clarify_answer,
        route_to_ask_answer=route_to_ask_answer,
    ) or is_capabilities_help_answer(text)


__all__ = [
    "is_capabilities_help_answer",
    "is_clarification_answer",
    "is_clarification_or_capability_confirmation_answer",
]
