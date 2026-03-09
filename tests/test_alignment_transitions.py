from collections import deque
from dataclasses import replace

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState, ProvenanceType
from testbot.sat_chatbot_memory_v2 import (
    ASSIST_ALTERNATIVES_ANSWER,
    evaluate_alignment_decision,
    stage_answer,
)
from testbot.stage_transitions import (
    BACKGROUND_INGESTION_PROGRESS_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    validate_answer_commit_post,
)


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
        used_memory_refs=["1@2025-01-01T00:00:00Z"],
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


def test_validate_answer_commit_post_rejects_missing_alignment_dimension() -> None:
    state = _base_state()
    state.alignment_decision["dimensions"].pop("cost_latency_budget")

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "alignment_dimensions_present" in result.failures


def test_validate_answer_commit_post_allows_progressive_clarifier_when_factual_grounding_fails() -> None:
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
        resolved_intent="memory_recall",
    )

    result = validate_answer_commit_post(state)

    assert result.passed


def test_validate_answer_commit_post_progressive_fallback_enforced_allows_explicit_uncertainty_when_low_confidence() -> None:
    invariant_decisions = {
        **_base_state().invariant_decisions,
        "answer_contract_valid": False,
        "answer_mode": "dont-know",
    }
    alignment_decision = {
        **_base_state().alignment_decision,
        "final_alignment_decision": "allow",
    }
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        draft_answer="",
        final_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )

    result = validate_answer_commit_post(state)

    assert result.passed, "progressive fallback should allow approved fallback path when confidence is low"


def test_validate_answer_commit_post_progressive_fallback_enforced_rejects_direct_answer_when_low_confidence() -> None:
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        draft_answer="",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "inv_002_progressive_fallback_enforced" in result.failures


def test_validate_answer_commit_post_progressive_fallback_enforced_allows_confident_valid_contract_path() -> None:
    state = _base_state()

    result = validate_answer_commit_post(state)

    assert result.passed, "progressive fallback should permit confident answers with a valid contract"

def test_validate_answer_commit_post_allows_assist_fallback_when_general_knowledge_contract_fails() -> None:
    state = replace(
        _base_state(),
        final_answer=ASSIST_ALTERNATIVES_ANSWER,
        invariant_decisions={
            **_base_state().invariant_decisions,
            "general_knowledge_contract_valid": False,
            "answer_mode": "assist",
        },
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert result.passed


def test_validate_answer_commit_post_rejects_memory_grounded_fallback_when_general_knowledge_contract_fails() -> None:
    state = replace(
        _base_state(),
        final_answer=FALLBACK_ANSWER,
        invariant_decisions={
            **_base_state().invariant_decisions,
            "general_knowledge_contract_valid": False,
            "answer_mode": "memory-grounded",
        },
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "fallback"},
    )

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "inv_003_general_knowledge_contract_enforced" in result.failures


def test_validate_answer_commit_post_allows_dont_know_fallback_when_general_knowledge_contract_fails() -> None:
    state = replace(
        _base_state(),
        final_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        invariant_decisions={
            **_base_state().invariant_decisions,
            "general_knowledge_contract_valid": False,
            "answer_mode": "dont-know",
            "answer_contract_valid": False,
        },
        confidence_decision={"context_confident": False},
        draft_answer="",
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert result.passed


def test_validate_answer_commit_post_allows_pending_lookup_progress_response_when_general_knowledge_contract_fails() -> None:
    state = replace(
        _base_state(),
        final_answer=BACKGROUND_INGESTION_PROGRESS_ANSWER,
        confidence_decision={"context_confident": False, "background_ingestion_in_progress": True},
        invariant_decisions={
            **_base_state().invariant_decisions,
            "answer_contract_valid": False,
            "general_knowledge_contract_valid": False,
            "answer_mode": "assist",
        },
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert result.passed


def test_validate_answer_commit_post_allows_deny_when_safety_dimension_fails() -> None:
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

    result = validate_answer_commit_post(state)

    assert result.passed




def test_validate_answer_commit_post_rejects_knowing_mode_without_provenance_metadata() -> None:
    state = replace(
        _base_state(),
        invariant_decisions={**_base_state().invariant_decisions, "answer_mode": "memory-grounded"},
        provenance_types=[ProvenanceType.INFERENCE],
        used_memory_refs=[],
        used_source_evidence_refs=[],
        basis_statement="",
    )

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "knowing_mode_requires_provenance_metadata" in result.failures


def test_validate_answer_commit_post_allows_knowing_mode_with_provenance_metadata() -> None:
    state = replace(
        _base_state(),
        invariant_decisions={**_base_state().invariant_decisions, "answer_mode": "memory-grounded"},
        provenance_types=[ProvenanceType.MEMORY, ProvenanceType.INFERENCE],
        used_memory_refs=["d-1@2025-01-01T00:00:00Z"],
        basis_statement="Answer synthesized from reranked memory context.",
    )

    result = validate_answer_commit_post(state)

    assert result.passed


def test_validate_answer_commit_post_rejects_unknowing_mode_without_explicit_uncertainty_fallback() -> None:
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        invariant_decisions={**_base_state().invariant_decisions, "answer_mode": "dont-know", "answer_contract_valid": False},
        final_answer="Need more details.",
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "unknowing_mode_requires_explicit_uncertainty_fallback" in result.failures


def test_validate_answer_commit_post_allows_unknowing_mode_with_explicit_uncertainty_response() -> None:
    state = replace(
        _base_state(),
        confidence_decision={"context_confident": False},
        invariant_decisions={**_base_state().invariant_decisions, "answer_mode": "dont-know", "answer_contract_valid": False},
        final_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert result.passed
def test_validate_answer_commit_post_rejects_missing_provenance_dimension_for_non_trivial_answer() -> None:
    state = _base_state()
    state.alignment_decision["dimensions"].pop("provenance_transparency")

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "alignment_dimensions_present" in result.failures


class _InvalidContractLLM:
    class _Response:
        content = "Topology studies shape and continuity across spaces."

    def invoke(self, _msgs):
        return self._Response()


class _UnlabeledGeneralKnowledgeLLM:
    class _Response:
        content = "Life is a characteristic that distinguishes biological processes from nonliving matter. doc_id: gk-1 ts: 2026-01-01T00:00:00Z"

    def invoke(self, _msgs):
        return self._Response()


def test_stage_answer_non_memory_invalid_gk_contract_routes_to_safe_fallback_and_passes_post_validation() -> None:
    state = PipelineState(
        user_input="What is life?",
        rewritten_query="what is life",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.2,
            "general_knowledge_support": 0,
        },
        resolved_intent="knowledge_question",
    )

    answer_state = stage_answer(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=None,
    )

    assert answer_state.invariant_decisions["general_knowledge_contract_valid"] is False
    assert answer_state.final_answer == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert answer_state.invariant_decisions["answer_mode"] == "dont-know"

    result = validate_answer_commit_post(answer_state)

    assert result.passed is True


def test_stage_answer_social_statement_with_invalid_gk_contract_degrades_to_uncertainty_fallback() -> None:
    state = PipelineState(
        user_input="My name is Sebastian",
        rewritten_query="my name is sebastian",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "general_knowledge_confidence": 0.0,
            "general_knowledge_support": 0,
        },
        resolved_intent="knowledge_question",
    )

    answer_state = stage_answer(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=None,
    )

    assert answer_state.invariant_decisions["general_knowledge_contract_valid"] is False
    assert answer_state.final_answer == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert answer_state.invariant_decisions["answer_mode"] == "dont-know"
    assert validate_answer_commit_post(answer_state).passed is True


def test_validate_answer_commit_post_rejects_non_fallback_factual_answer_when_gk_contract_invalid() -> None:
    state = replace(
        _base_state(),
        final_answer="Life is the condition that distinguishes organisms from inorganic matter.",
        invariant_decisions={
            **_base_state().invariant_decisions,
            "general_knowledge_contract_valid": False,
            "answer_mode": "memory-grounded",
        },
        alignment_decision={**_base_state().alignment_decision, "final_alignment_decision": "allow"},
    )

    result = validate_answer_commit_post(state)

    assert not result.passed
    assert "inv_003_general_knowledge_contract_enforced" in result.failures


def test_stage_answer_memory_hit_without_ambiguity_uses_contract_safe_recovery_answer() -> None:
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

    assert answered.final_answer.startswith("From memory, I found:")
    assert "doc_id: d-1" in answered.final_answer
    assert answered.invariant_decisions["answer_mode"] == "memory-grounded"
    assert answered.alignment_decision["final_alignment_decision"] == "allow"
    assert validate_answer_commit_post(answered).passed





def test_evaluate_alignment_decision_missing_required_citation_sets_citation_validity_to_zero() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="You said hi yesterday.",
        final_answer="You said hi yesterday.",
        confidence_decision={
            "context_confident": True,
            "scored_candidates": [{"final_score": 0.91}, {"final_score": 0.42}],
            "min_margin_to_second": 0.1,
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
    )

    raw = decision["dimension_inputs"]["raw"]
    normalized = decision["dimension_inputs"]["normalized"]
    assert raw["citation_required_for_mode"] is True
    assert raw["citation_check_applicable"] is True
    assert normalized["citation_validity"] == 0.0
    assert decision["final_alignment_decision"] == "fallback"


def test_evaluate_alignment_decision_no_claims_fallback_does_not_inflate_citation_or_provenance() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="",
        final_answer=NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
        confidence_decision={"context_confident": False},
        claims=[],
        provenance_types=[ProvenanceType.UNKNOWN],
        basis_statement="",
    )

    raw = decision["dimension_inputs"]["raw"]
    normalized = decision["dimension_inputs"]["normalized"]
    assert raw["citation_required_for_mode"] is False
    assert raw["citation_check_applicable"] is False
    assert normalized["citation_validity"] == 0.0
    assert decision["dimensions"]["provenance_transparency"] == 0.3333
    assert decision["final_alignment_decision"] == "allow"


def test_evaluate_alignment_decision_with_required_citation_allows_when_other_signals_are_strong() -> None:
    decision = evaluate_alignment_decision(
        user_input="what did i say yesterday",
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        confidence_decision={
            "context_confident": True,
            "scored_candidates": [{"final_score": 0.91}, {"final_score": 0.42}],
            "min_margin_to_second": 0.1,
        },
        claims=["You said hi yesterday."],
        provenance_types=[ProvenanceType.MEMORY],
        basis_statement="Based on memory card doc_id: 1.",
    )

    raw = decision["dimension_inputs"]["raw"]
    normalized = decision["dimension_inputs"]["normalized"]
    assert raw["citation_required_for_mode"] is True
    assert raw["citation_check_applicable"] is True
    assert normalized["citation_validity"] == 1.0
    assert decision["final_alignment_decision"] == "allow"


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
