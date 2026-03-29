from __future__ import annotations

from dataclasses import replace

import pytest

from testbot.answer_contract_constants import (
    ASSIST_ALTERNATIVES_ANSWER,
    BACKGROUND_INGESTION_PROGRESS_ANSWER,
    CLARIFY_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    ROUTE_TO_ASK_ANSWER,
)
from testbot.answer_stage_semantics import expected_alignment_decisions_for_final_answer
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.stage_transitions import validate_answer_commit_post


def _base_state() -> PipelineState:
    return PipelineState(
        user_input="test",
        retrieval_candidates=[CandidateHit(doc_id="d-1", score=0.9, ts="2025-01-01T00:00:00Z", card_type="memory")],
        reranked_hits=[CandidateHit(doc_id="d-1", score=0.9, ts="2025-01-01T00:00:00Z", card_type="memory")],
        confidence_decision={"context_confident": True},
        resolved_intent="memory_recall",
    )


@pytest.mark.parametrize(
    ("final_answer", "answer_mode", "fallback_action", "alignment"),
    [
        (DENY_ANSWER, "deny", "NONE", "deny"),
        (FALLBACK_ANSWER, "dont-know", "ANSWER_UNKNOWN", "fallback"),
        (CLARIFY_ANSWER, "clarify", "ASK_CLARIFYING_QUESTION", "allow"),
        (ROUTE_TO_ASK_ANSWER, "clarify", "ROUTE_TO_ASK", "allow"),
        (ASSIST_ALTERNATIVES_ANSWER, "assist", "OFFER_CAPABILITY_ALTERNATIVES", "allow"),
        (NON_KNOWLEDGE_UNCERTAINTY_ANSWER, "dont-know", "ANSWER_GENERAL_KNOWLEDGE", "allow"),
        (BACKGROUND_INGESTION_PROGRESS_ANSWER, "dont-know", "ANSWER_UNKNOWN", "allow"),
        (
            "From memory, I found: release prep requires changelog review.",
            "memory-grounded",
            "ANSWER_FROM_MEMORY",
            "fallback",
        ),
    ],
)
def test_canonical_answer_semantics_define_alignment_expectations(
    final_answer: str,
    answer_mode: str,
    fallback_action: str,
    alignment: str,
) -> None:
    state = replace(
        _base_state(),
        final_answer=final_answer,
        claims=(["release prep requires changelog review"] if final_answer.startswith("From memory, I found:") else []),
        provenance_types=([ProvenanceType.MEMORY] if final_answer.startswith("From memory, I found:") else []),
        basis_statement=("Grounded in memory." if final_answer.startswith("From memory, I found:") else "No factual claims."),
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": answer_mode,
            "fallback_action": fallback_action,
        },
        alignment_decision={
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 0.9,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0 if final_answer.startswith("From memory, I found:") else 0.0,
            },
            "final_alignment_decision": alignment,
        },
    )

    assert alignment in expected_alignment_decisions_for_final_answer(final_answer)
    result = validate_answer_commit_post(state)
    assert "alignment_decision_consistent" not in result.failures


def test_canonical_answer_semantics_reject_incompatible_alignment_decision() -> None:
    state = replace(
        _base_state(),
        final_answer=CLARIFY_ANSWER,
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": "clarify",
            "fallback_action": "ASK_CLARIFYING_QUESTION",
        },
        alignment_decision={
            "dimensions": {
                "factual_grounding_reliability": "not_applicable",
                "safety_compliance_strictness": 1.0,
                "response_utility": 0.8,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 0.0,
            },
            "final_alignment_decision": "fallback",
        },
    )

    assert "fallback" not in expected_alignment_decisions_for_final_answer(CLARIFY_ANSWER)
    result = validate_answer_commit_post(state)
    assert "alignment_decision_consistent" in result.failures

