"""Canonical reject taxonomy for decision and debug payload signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RejectPartition = Literal["intent", "retrieval", "rerank", "contract", "policy", "temporal", "none"]

RejectCode = Literal[
    "NONE",
    "CONTEXT_CONF_BELOW_THRESHOLD",
    "TEMPORAL_REFERENCE_UNRESOLVED",
    "NO_CITABLE_MEMORY_EVIDENCE",
    "AMBIGUOUS_MEMORY_CANDIDATES",
    "ANSWER_CONTRACT_GROUNDING_FAIL",
    "GK_CONTRACT_MARKER_FAIL",
    "POLICY_SAFETY_DENY",
]


@dataclass(frozen=True)
class RejectSignal:
    reject_code: RejectCode
    partition: RejectPartition
    score: float
    threshold: float
    margin: float
    reason: str


def derive_reject_signal(
    *,
    intent_label: str,
    answer_mode: str,
    fallback_action: str,
    context_confident: bool,
    context_score: float,
    hit_count: int,
    ambiguity_detected: bool,
    answer_contract_valid: bool,
    general_knowledge_contract_valid: bool,
) -> RejectSignal:
    """Return deterministic machine-oriented reject signal with human-readable reason."""

    def _signal(
        *,
        code: RejectCode,
        partition: RejectPartition,
        score: float,
        threshold: float,
        reason: str,
    ) -> RejectSignal:
        return RejectSignal(
            reject_code=code,
            partition=partition,
            score=round(score, 4),
            threshold=round(threshold, 4),
            margin=round(score - threshold, 4),
            reason=reason,
        )

    if answer_mode == "deny":
        return _signal(
            code="POLICY_SAFETY_DENY",
            partition="policy",
            score=0.0,
            threshold=1.0,
            reason="request blocked by safety or policy checks",
        )

    if intent_label == "time_query" and (answer_mode in {"clarify", "dont-know"} or fallback_action == "ANSWER_UNKNOWN"):
        return _signal(
            code="TEMPORAL_REFERENCE_UNRESOLVED",
            partition="temporal",
            score=float(hit_count),
            threshold=1.0,
            reason="unable to resolve temporal reference with reliable evidence",
        )

    if answer_mode == "clarify" or fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        if hit_count == 0:
            return _signal(
                code="NO_CITABLE_MEMORY_EVIDENCE",
                partition="retrieval",
                score=0.0,
                threshold=1.0,
                reason="no memory fragments were retrieved for this request",
            )
        if ambiguity_detected:
            return _signal(
                code="AMBIGUOUS_MEMORY_CANDIDATES",
                partition="rerank",
                score=0.0,
                threshold=1.0,
                reason="retrieved memory fragments were ambiguous",
            )
        if not context_confident:
            return _signal(
                code="CONTEXT_CONF_BELOW_THRESHOLD",
                partition="rerank",
                score=context_score,
                threshold=1.0,
                reason="retrieved memory fragments were low-confidence",
            )

    if answer_mode == "dont-know" or fallback_action == "ANSWER_UNKNOWN":
        return _signal(
            code="NO_CITABLE_MEMORY_EVIDENCE",
            partition="retrieval",
            score=float(hit_count),
            threshold=1.0,
            reason="insufficient reliable memory to answer directly",
        )

    if answer_mode == "assist" or fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        if not answer_contract_valid:
            return _signal(
                code="ANSWER_CONTRACT_GROUNDING_FAIL",
                partition="contract",
                score=0.0,
                threshold=1.0,
                reason="answer-contract rejection: draft did not satisfy grounding/citation requirements",
            )
        if not general_knowledge_contract_valid:
            return _signal(
                code="GK_CONTRACT_MARKER_FAIL",
                partition="contract",
                score=0.0,
                threshold=1.0,
                reason="general-knowledge contract rejection: response did not satisfy marker/confidence policy",
            )
        if ambiguity_detected:
            return _signal(
                code="AMBIGUOUS_MEMORY_CANDIDATES",
                partition="rerank",
                score=0.0,
                threshold=1.0,
                reason="retrieved memory fragments were ambiguous; offered capability alternatives",
            )
        if not context_confident:
            return _signal(
                code="CONTEXT_CONF_BELOW_THRESHOLD",
                partition="rerank",
                score=context_score,
                threshold=1.0,
                reason="retrieved memory fragments were low-confidence for a direct answer",
            )
        if context_confident and hit_count > 0:
            return _signal(
                code="GK_CONTRACT_MARKER_FAIL",
                partition="contract",
                score=0.0,
                threshold=1.0,
                reason="policy/contract rejected direct answer despite confident retrieved context",
            )

    return _signal(code="NONE", partition="none", score=1.0, threshold=1.0, reason="none")
