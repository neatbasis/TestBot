"""Pure scoring and decision logic modules."""

from testbot.logic.alignment import (
    ALIGNMENT_OBJECTIVE_VERSION,
    GENERAL_KNOWLEDGE_CONFIDENCE_MIN,
    GENERAL_KNOWLEDGE_MARKER_PREFIX,
    GENERAL_KNOWLEDGE_SUPPORT_MIN,
    assess_general_knowledge_contract,
    evaluate_alignment_decision,
    extract_claims,
    has_general_knowledge_marker,
    has_required_memory_citation,
    is_non_trivial_answer,
    is_unsafe_user_request,
    passes_general_knowledge_confidence_gate,
    raw_claim_like_text_detected,
    response_contains_claims,
    validate_answer_contract,
    validate_general_knowledge_contract,
)

__all__ = [
    "ALIGNMENT_OBJECTIVE_VERSION",
    "GENERAL_KNOWLEDGE_CONFIDENCE_MIN",
    "GENERAL_KNOWLEDGE_MARKER_PREFIX",
    "GENERAL_KNOWLEDGE_SUPPORT_MIN",
    "assess_general_knowledge_contract",
    "evaluate_alignment_decision",
    "extract_claims",
    "has_general_knowledge_marker",
    "has_required_memory_citation",
    "is_non_trivial_answer",
    "is_unsafe_user_request",
    "passes_general_knowledge_confidence_gate",
    "raw_claim_like_text_detected",
    "response_contains_claims",
    "validate_answer_contract",
    "validate_general_knowledge_contract",
]
