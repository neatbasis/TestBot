from dataclasses import replace

from testbot.pipeline_state import PipelineState
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
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 1.0,
                "cost_latency_budget": 1.0,
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


def test_validate_answer_post_allows_fallback_when_factual_grounding_fails() -> None:
    invariant_decisions = {**_base_state().invariant_decisions, "answer_contract_valid": True, "answer_mode": "dont-know"}
    alignment_decision = {
        "objective_version": "2026-03-01.v1",
        "dimensions": {
            "factual_grounding_reliability": 0.0,
            "safety_compliance_strictness": 1.0,
            "response_utility": 0.4,
            "cost_latency_budget": 1.0,
        },
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

    assert result.passed


def test_validate_answer_post_allows_deny_when_safety_dimension_fails() -> None:
    invariant_decisions = {**_base_state().invariant_decisions, "answer_mode": "deny"}
    alignment_decision = {
        "objective_version": "2026-03-01.v1",
        "dimensions": {
            "factual_grounding_reliability": 1.0,
            "safety_compliance_strictness": 0.0,
            "response_utility": 0.4,
            "cost_latency_budget": 1.0,
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
