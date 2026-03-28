"""Canonical answer-stage contract constants.

Owns stable fallback/clarification/assist answer strings consumed by answer-stage
services, alignment checks, and legacy compatibility wrappers.
"""

from __future__ import annotations

FALLBACK_ANSWER = "I don't know from memory."
DENY_ANSWER = "I can't comply with that request."
CLARIFY_ANSWER = "Can you clarify which memory and time window you mean?"
ROUTE_TO_ASK_ANSWER = "I can disambiguate this with a quick follow-up question."
ASSIST_ALTERNATIVES_ANSWER = (
    "I don't have enough reliable memory to answer directly. "
    "I can either help you reconstruct the timeline from what you remember, "
    "or suggest where to check next for the missing detail."
)
NON_KNOWLEDGE_UNCERTAINTY_ANSWER = (
    "I'm not fully confident in a reliable answer right now. "
    "I can offer a best-effort response and suggest a quick way to verify it."
)
BACKGROUND_INGESTION_PROGRESS_ANSWER = "I'm ingesting external sources in the background now…"

__all__ = [
    "ASSIST_ALTERNATIVES_ANSWER",
    "BACKGROUND_INGESTION_PROGRESS_ANSWER",
    "CLARIFY_ANSWER",
    "DENY_ANSWER",
    "FALLBACK_ANSWER",
    "NON_KNOWLEDGE_UNCERTAINTY_ANSWER",
    "ROUTE_TO_ASK_ANSWER",
]
