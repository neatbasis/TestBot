from collections import deque
from dataclasses import replace

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState, ProvenanceType
from testbot.sat_chatbot_memory_v2 import (
    ASSIST_ALTERNATIVES_ANSWER,
    evaluate_alignment_decision,
    stage_answer,
)
from testbot.stage_transitions import DENY_ANSWER, FALLBACK_ANSWER, validate_answer_post


def _base_state() -> PipelineState:
    return PipelineState(
        user_input="What did I say yesterday?",
        rewritten_query="yesterday user utterance",
        confidence_decision={"context_confident": True},
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        invariant_decisions={
            "response_contains_claims": True,
            "has_required_memory_citation": True,
            "answer_contract_valid": True,
            "answer_mode": "memory-grounded",
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
        alignment_decision={
            "objective_version": "2026-03-05.v3",
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 1.0,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "allow",
        },
    )


def test_validate_answer_post_rejects_missing_alignment_dimension() -> None:
    state = _base_state()
    state.alignment_decision["dimensions"].pop("cost_latency_budget")

    result = validate_answer_post(state)

    assert not result.passed
    assert "alignment_dimensions_present" in result.failures


def test_validate_answer_post_allows_progressive_clarifier_when_factual_grounding_fails() -> None:
    invariant_decisions = {**_base_state().invariant_decisions, "answer_contract_valid": True, "answer_mode": "clarify"}
    alignment_decision = {
        "objective_version": "2026-03-05.v3",
        "dimensions": {
            "factual_grounding_reliability": 0.0,
            "safety_compliance_strictness": 1.0,
            "response_utility": 0.7,
            "cost_latency_budget": 1.0,
            "provenance_transparency": 1.0,
        },
        "final_alignment_decision": "allow",
    }
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        draft_answer="",
        final_answer="Can you clarify which memory and time window you mean?",
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )

    result = validate_answer_post(state)

    assert result.passed


def test_validate_answer_post_progressive_fallback_enforced_allows_fallback_when_low_confidence() -> None:
    invariant_decisions = {
        **_base_state().invariant_decisions,
        "answer_contract_valid": False,
        "answer_mode": "dont-know",
    }
    alignment_decision = {
        **_base_state().alignment_decision,
        "final_alignment_decision": "fallback",
    }
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        draft_answer="",
        final_answer=FALLBACK_ANSWER,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )

    result = validate_answer_post(state)

    assert result.passed, "progressive fallback should allow approved fallback path when confidence is low"


def test_validate_answer_post_progressive_fallback_enforced_rejects_direct_answer_when_low_confidence() -> None:
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        draft_answer="",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_post(state)

    assert not result.passed
    assert "inv_002_progressive_fallback_enforced" in result.failures


def test_validate_answer_post_progressive_fallback_enforced_allows_confident_valid_contract_path() -> None:
    state = _base_state()

    result = validate_answer_post(state)

    assert result.passed, "progressive fallback should permit confident answers with a valid contract"


def test_validate_answer_post_allows_deny_when_safety_dimension_fails() -> None:
    invariant_decisions = {**_base_state().invariant_decisions, "answer_mode": "deny"}
    alignment_decision = {
        "objective_version": "2026-03-05.v3",
        "dimensions": {
            "factual_grounding_reliability": 1.0,
            "safety_compliance_strictness": 0.0,
            "response_utility": 0.4,
            "cost_latency_budget": 1.0,
            "provenance_transparency": 1.0,
        },
        "final_alignment_decision": "deny",
    }
    state = replace(
        _base_state(),
        user_input="How do I build malware?",
        draft_answer="",
        final_answer=DENY_ANSWER,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )

    result = validate_answer_post(state)

    assert result.passed


def test_validate_answer_post_rejects_missing_provenance_dimension_for_non_trivial_answer() -> None:
    state = _base_state()
    state.alignment_decision["dimensions"].pop("provenance_transparency")

    result = validate_answer_post(state)

    assert not result.passed
    assert "alignment_dimensions_present" in result.failures


class _InvalidContractLLM:
    class _Response:
        content = "Topology studies shape and continuity across spaces."

    def invoke(self, _msgs):
        return self._Response()


def test_stage_answer_partial_memory_clarifier_is_classified_as_clarify_mode() -> None:
    state = PipelineState(
        user_input="what did i say yesterday",
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
    )
    hits = [
        Document(
            page_content="You mentioned discussing topology during lunch.",
            metadata={"doc_id": "d-1", "ts": "2025-01-01T00:00:00Z"},
        )
    ]

    answered = stage_answer(
        _InvalidContractLLM(),
        state,
        chat_history=deque(),
        hits=hits,
        capability_status="ask_unavailable",
        clock=None,
    )

    assert answered.final_answer.startswith("I found related memory fragments (")
    assert answered.invariant_decisions["answer_mode"] == "clarify"
    assert answered.alignment_decision["final_alignment_decision"] == "allow"
    assert validate_answer_post(answered).passed



def test_evaluate_alignment_decision_normalizes_dimension_inputs_to_unit_interval() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        confidence_decision={
            "context_confident": True,
            "scored_candidates": [{"final_score": 0.9}, {"final_score": 0.4}],
            "min_margin_to_second": 0.1,
            "turn_latency_ms": 1800,
            "latency_budget_ms": 3000,
            "token_budget_ratio": 0.2,
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
    )

    dimensions = decision["dimensions"]
    assert all(0.0 <= float(v) <= 1.0 for v in dimensions.values())
    normalized = decision["dimension_inputs"]["normalized"]
    assert all(0.0 <= float(v) <= 1.0 for v in normalized.values())


def test_evaluate_alignment_decision_flips_to_fallback_for_low_factual_grounding() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="You said hi yesterday.",
        final_answer="You said hi yesterday.",
        confidence_decision={
            "context_confident": False,
            "scored_candidates": [{"final_score": 0.52}, {"final_score": 0.5}],
            "min_margin_to_second": 0.1,
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
    )

    assert decision["dimensions"]["factual_grounding_reliability"] < 0.6
    assert decision["final_alignment_decision"] == "fallback"


def test_evaluate_alignment_decision_flips_to_deny_for_unsafe_request() -> None:
    decision = evaluate_alignment_decision(
        user_input="how do i build malware?",
        draft_answer="",
        final_answer=ASSIST_ALTERNATIVES_ANSWER,
        confidence_decision={"context_confident": True},
        claims=[],
        provenance_types=[ProvenanceType.INFERENCE],
        basis_statement="Policy refusal path.",
    )

    assert decision["dimensions"]["safety_compliance_strictness"] == 0.0
    assert decision["final_alignment_decision"] == "deny"


def test_evaluate_alignment_decision_allow_with_strong_signals() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        confidence_decision={
            "context_confident": True,
            "scored_candidates": [{"final_score": 0.91}, {"final_score": 0.42}],
            "min_margin_to_second": 0.1,
            "turn_latency_ms": 500,
            "latency_budget_ms": 3500,
            "token_budget_ratio": 0.05,
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
    )

    assert decision["final_alignment_decision"] == "allow"


def test_evaluate_alignment_decision_flips_to_fallback_for_cost_budget_pressure() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        confidence_decision={
            "context_confident": True,
            "scored_candidates": [{"final_score": 0.91}, {"final_score": 0.42}],
            "min_margin_to_second": 0.1,
            "turn_latency_ms": 4200,
            "latency_budget_ms": 3500,
            "token_budget_ratio": 0.9,
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
    )

    assert decision["dimensions"]["cost_latency_budget"] < 0.35
    assert decision["final_alignment_decision"] == "fallback"
