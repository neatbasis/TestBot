from __future__ import annotations

import re
from collections.abc import Callable
from typing import Mapping

from testbot.pipeline_state import ConfidenceDecision, ProvenanceType
from testbot.stage_transitions import (
    ASSIST_ALTERNATIVES_ANSWER,
    BACKGROUND_INGESTION_PROGRESS_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
)

GENERAL_KNOWLEDGE_MARKER_PREFIX = "General definition (not from your memory):"
GENERAL_KNOWLEDGE_CONFIDENCE_MIN = 0.85
GENERAL_KNOWLEDGE_SUPPORT_MIN = 2
ALIGNMENT_OBJECTIVE_VERSION = "2026-03-10.v4"

CLARIFY_ANSWER = "Can you clarify which memory and time window you mean?"
ROUTE_TO_ASK_ANSWER = "I can disambiguate this with a quick follow-up question."


def is_non_trivial_answer(text: str) -> bool:
    normalized = (text or "").strip()
    return bool(normalized) and normalized not in {
        FALLBACK_ANSWER,
        DENY_ANSWER,
        CLARIFY_ANSWER,
        ROUTE_TO_ASK_ANSWER,
        ASSIST_ALTERNATIVES_ANSWER,
    }


def extract_claims(text: str) -> list[str]:
    if not is_non_trivial_answer(text):
        return []
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return parts[:4]


def response_contains_claims(text: str) -> bool:
    return bool(extract_claims(text))


def raw_claim_like_text_detected(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if normalized in {FALLBACK_ANSWER, CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER, ASSIST_ALTERNATIVES_ANSWER}:
        return False
    return bool(re.search(r"[A-Za-z0-9].{8,}", normalized))


def has_required_memory_citation(text: str) -> bool:
    citation_pattern = re.compile(r"doc_id\s*[:=]\s*[^,\]\)\n]+.*?ts\s*[:=]\s*[^,\]\)\n]+", re.IGNORECASE)
    return bool(citation_pattern.search(text or ""))


def validate_answer_contract(text: str) -> bool:
    if not raw_claim_like_text_detected(text):
        return True
    return has_required_memory_citation(text)


def has_general_knowledge_marker(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith(GENERAL_KNOWLEDGE_MARKER_PREFIX.lower())


def passes_general_knowledge_confidence_gate(confidence_decision: Mapping[str, object]) -> bool:
    confidence = float(confidence_decision.get("general_knowledge_confidence", 0.0) or 0.0)
    support_count = int(confidence_decision.get("general_knowledge_support", 0) or 0)
    return confidence >= GENERAL_KNOWLEDGE_CONFIDENCE_MIN and support_count >= GENERAL_KNOWLEDGE_SUPPORT_MIN


def validate_general_knowledge_contract(
    text: str,
    *,
    provenance_types: list[ProvenanceType],
    confidence_decision: Mapping[str, object],
) -> bool:
    if not response_contains_claims(text):
        return True
    if ProvenanceType.GENERAL_KNOWLEDGE not in provenance_types:
        return True
    return has_general_knowledge_marker(text) and passes_general_knowledge_confidence_gate(confidence_decision)


def assess_general_knowledge_contract(
    text: str,
    *,
    provenance_types: list[ProvenanceType],
    confidence_decision: Mapping[str, object],
    is_clarification_answer: Callable[[str], bool] | None = None,
    is_capabilities_help_answer: Callable[[str], bool] | None = None,
) -> tuple[bool, str, str]:
    if is_clarification_answer is not None and is_clarification_answer(text):
        return True, "not_applicable", "clarification_response"
    if text in {
        ASSIST_ALTERNATIVES_ANSWER,
        NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        FALLBACK_ANSWER,
        BACKGROUND_INGESTION_PROGRESS_ANSWER,
        DENY_ANSWER,
    } or (is_capabilities_help_answer is not None and is_capabilities_help_answer(text)):
        return True, "not_applicable", "exempt_response_type"
    if not response_contains_claims(text):
        return True, "not_applicable", "no_claims"
    if ProvenanceType.GENERAL_KNOWLEDGE not in provenance_types:
        return True, "not_applicable", "no_general_knowledge_provenance"
    return (
        validate_general_knowledge_contract(
            text,
            provenance_types=provenance_types,
            confidence_decision=confidence_decision,
        ),
        "applicable",
        "none",
    )


def is_unsafe_user_request(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(re.search(r"\b(bypass|exploit|weapon|harm|poison|malware)\b", lowered))


def evaluate_alignment_decision(
    *,
    user_input: str,
    draft_answer: str,
    final_answer: str,
    confidence_decision: Mapping[str, object],
    claims: list[str],
    provenance_types: list[ProvenanceType],
    basis_statement: str,
    is_clarification_answer: Callable[[str], bool] | None = None,
    is_capabilities_help_answer: Callable[[str], bool] | None = None,
) -> dict[str, object]:
    typed_confidence = ConfidenceDecision.from_mapping(confidence_decision)

    def _clamp01(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 4)

    def _candidate_margin_normalized() -> tuple[float, float, float]:
        scored_candidates = typed_confidence.typed_scored_candidates()
        if len(scored_candidates) < 2:
            return 0.0, 0.0, 0.0
        first = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
        second = scored_candidates[1] if isinstance(scored_candidates[1], dict) else {}
        top_score = float(first.get("final_score", 0.0) or 0.0)
        second_score = float(second.get("final_score", 0.0) or 0.0)
        observed_margin = max(0.0, top_score - second_score)
        required_margin = float(typed_confidence.min_margin_to_second or 0.05)
        normalized_margin = _clamp01(observed_margin / required_margin) if required_margin > 0.0 else 1.0
        return observed_margin, required_margin, normalized_margin

    _, general_knowledge_contract_applicability, contract_exempt_reason = assess_general_knowledge_contract(
        final_answer,
        provenance_types=provenance_types,
        confidence_decision=confidence_decision,
        is_clarification_answer=is_clarification_answer,
        is_capabilities_help_answer=is_capabilities_help_answer,
    )
    contract_exempt_response = contract_exempt_reason in {"clarification_response", "exempt_response_type"}
    has_claims = response_contains_claims(draft_answer)
    raw_claim_text_detected = raw_claim_like_text_detected(draft_answer)
    has_citation = has_required_memory_citation(draft_answer)
    context_confident = bool(typed_confidence.context_confident)
    unsafe_request = is_unsafe_user_request(user_input)
    observed_margin, required_margin, confidence_margin_normalized = _candidate_margin_normalized()

    citation_required_for_mode = raw_claim_text_detected and not contract_exempt_response
    citation_check_applicable = citation_required_for_mode
    grounding_dimension_applicability = "applicable"
    if contract_exempt_response and not citation_required_for_mode:
        grounding_dimension_applicability = "not_applicable"

    citation_validity: float | str
    confidence_margin_component: float | str
    factual_grounding_reliability: float | str
    if grounding_dimension_applicability == "not_applicable":
        citation_validity = "not_applicable"
        confidence_margin_component = "not_applicable"
        factual_grounding_reliability = "not_applicable"
    else:
        if citation_required_for_mode:
            citation_validity = 1.0 if has_citation else 0.0
        elif raw_claim_text_detected:
            citation_validity = 0.5
        else:
            citation_validity = 0.0
        confidence_margin_component = confidence_margin_normalized
        factual_grounding_reliability = _clamp01((0.65 * citation_validity) + (0.35 * confidence_margin_component))
    safety_compliance_strictness = 0.0 if (unsafe_request and final_answer != DENY_ANSWER) else 1.0

    fallback_mode_score = 1.0
    if final_answer == DENY_ANSWER:
        fallback_mode_score = 0.0
    elif final_answer == FALLBACK_ANSWER:
        fallback_mode_score = 0.25
    elif contract_exempt_response:
        fallback_mode_score = 0.7

    intent_fulfillment_proxy = 1.0 if context_confident and final_answer not in {"", FALLBACK_ANSWER, DENY_ANSWER} else 0.45
    if contract_exempt_response:
        intent_fulfillment_proxy = 0.75
    response_utility = _clamp01((0.5 * fallback_mode_score) + (0.5 * intent_fulfillment_proxy))

    observed_latency_ms = float(typed_confidence.turn_latency_ms or 0.0)
    latency_budget_ms = float(typed_confidence.latency_budget_ms or 3500.0)
    latency_score = 1.0 if observed_latency_ms <= 0.0 else _clamp01(1.0 - (observed_latency_ms / latency_budget_ms))
    token_budget_ratio = float(typed_confidence.token_budget_ratio or 0.0)
    token_budget_score = 1.0 if token_budget_ratio <= 0.0 else _clamp01(1.0 - token_budget_ratio)
    cost_latency_budget = _clamp01(min(latency_score, token_budget_score))

    required_provenance_checks = {
        "claims_non_empty": bool(claims),
        "provenance_types_non_empty": bool(provenance_types),
        "basis_statement_non_empty": bool((basis_statement or "").strip()),
    }
    passed_required_checks = sum(1 for passed in required_provenance_checks.values() if passed)
    provenance_transparency = 0.0 if not is_non_trivial_answer(final_answer) else _clamp01(
        passed_required_checks / float(len(required_provenance_checks))
    )

    if safety_compliance_strictness < 1.0:
        final_alignment_decision = "deny"
    elif contract_exempt_response:
        final_alignment_decision = "allow"
    elif isinstance(factual_grounding_reliability, float) and factual_grounding_reliability < 0.6:
        final_alignment_decision = "fallback"
    elif response_utility < 0.5:
        final_alignment_decision = "fallback"
    elif provenance_transparency < 0.75:
        final_alignment_decision = "fallback"
    elif cost_latency_budget < 0.35:
        final_alignment_decision = "fallback"
    else:
        final_alignment_decision = "allow"

    return {
        "objective_version": ALIGNMENT_OBJECTIVE_VERSION,
        "dimensions": {
            "factual_grounding_reliability": factual_grounding_reliability,
            "safety_compliance_strictness": safety_compliance_strictness,
            "response_utility": response_utility,
            "cost_latency_budget": cost_latency_budget,
            "provenance_transparency": provenance_transparency,
        },
        "dimension_inputs": {
            "raw": {
                "has_claims": has_claims,
                "raw_claim_like_text_detected": raw_claim_text_detected,
                "has_required_memory_citation": has_citation,
                "citation_required_for_mode": citation_required_for_mode,
                "citation_check_applicable": citation_check_applicable,
                "grounding_dimension_applicability": grounding_dimension_applicability,
                "general_knowledge_contract_applicability": general_knowledge_contract_applicability,
                "contract_exempt_reason": contract_exempt_reason,
                "context_confident": context_confident,
                "unsafe_request": unsafe_request,
                "confidence_margin_observed": round(observed_margin, 4),
                "confidence_margin_required": round(required_margin, 4),
                "fallback_mode_score": fallback_mode_score,
                "intent_fulfillment_proxy": intent_fulfillment_proxy,
                "turn_latency_ms": observed_latency_ms,
                "latency_budget_ms": latency_budget_ms,
                "token_budget_ratio": token_budget_ratio,
                "provenance_checks": required_provenance_checks,
            },
            "normalized": {
                "citation_validity": citation_validity,
                "confidence_margin_normalized": confidence_margin_component,
                "fallback_mode_score": fallback_mode_score,
                "intent_fulfillment_proxy": intent_fulfillment_proxy,
                "latency_score": latency_score,
                "token_budget_score": token_budget_score,
                "provenance_completeness": provenance_transparency,
            },
        },
        "final_alignment_decision": final_alignment_decision,
    }
