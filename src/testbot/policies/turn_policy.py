"""Canonical owner for deterministic turn-policy confidence helpers."""

from __future__ import annotations

from testbot.intent_router import IntentType
from testbot.retrieval_routing import is_definitional_query_form

INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD = 0.75
RETRIEVAL_SCORE_THRESHOLD = 0.0


def intent_classifier_confidence(
    *,
    utterance: str,
    predicted_intent: IntentType,
    confidence_threshold: float = INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
) -> float:
    normalized = (utterance or "").strip().lower()
    if not normalized:
        return confidence_threshold

    if predicted_intent == IntentType.KNOWLEDGE_QUESTION and not is_definitional_query_form(normalized):
        return 0.82

    return 0.95


def minimal_confidence_decision_for_direct_answer(
    *,
    branch: str,
    base_confidence_decision: dict[str, object],
    retrieval_score_threshold: float = RETRIEVAL_SCORE_THRESHOLD,
) -> dict[str, object]:
    return {
        **base_confidence_decision,
        "context_confident": False,
        "ambiguity_detected": False,
        "ambiguous_candidates": [],
        "scored_candidates": [],
        "objective": "",
        "objective_version": "",
        "retrieval_branch": branch,
        "retrieval_candidates_considered": 0,
        "retrieval_returned_top_k": 0,
        "retrieval_threshold": retrieval_score_threshold,
    }


__all__ = [
    "INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD",
    "RETRIEVAL_SCORE_THRESHOLD",
    "intent_classifier_confidence",
    "minimal_confidence_decision_for_direct_answer",
]
