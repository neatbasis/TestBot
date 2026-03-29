"""Legacy-bridge coverage for deprecated stage transition aliases."""

from __future__ import annotations

from dataclasses import replace

from testbot.pipeline_state import CandidateHit, PipelineState
import pytest
from testbot.answer_contract_constants import CLARIFY_ANSWER
from testbot.stage_transitions import (
    validate_answer_commit_post,
    validate_answer_post,
    validate_observe_pre,
    validate_observe_turn_pre,
    validate_observe_turn_post,
    validate_observe_post,
    validate_policy_decide_post,
    validate_policy_decide_pre,
    validate_rerank_post,
    validate_rerank_pre,
)


def _base_state() -> PipelineState:
    return PipelineState(
        user_input="What did I say yesterday?",
        retrieval_candidates=[CandidateHit(doc_id="d-1", score=0.9, ts="2025-01-01T00:00:00Z", card_type="memory")],
        reranked_hits=[CandidateHit(doc_id="d-1", score=0.9, ts="2025-01-01T00:00:00Z", card_type="memory")],
        confidence_decision={"context_confident": True},
        invariant_decisions={"answer_contract_valid": True, "answer_mode": "memory-grounded"},
        alignment_decision={
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


def test_legacy_observe_aliases_forward_with_deprecation_warning() -> None:
    state = _base_state()

    with pytest.warns(DeprecationWarning, match="validate_observe_pre"):
        pre_alias = validate_observe_pre(state)
    pre_canonical = validate_observe_turn_pre(state)
    with pytest.warns(DeprecationWarning, match="validate_observe_post"):
        post_alias = validate_observe_post(state)
    post_canonical = validate_observe_turn_post(state)

    assert pre_alias.to_dict() == pre_canonical.to_dict()
    assert post_alias.to_dict() == post_canonical.to_dict()


def test_legacy_policy_aliases_forward_with_deprecation_warning() -> None:
    state = _base_state()

    with pytest.warns(DeprecationWarning, match="validate_rerank_pre"):
        pre_alias = validate_rerank_pre(state)
    pre_canonical = validate_policy_decide_pre(state)
    with pytest.warns(DeprecationWarning, match="validate_rerank_post"):
        post_alias = validate_rerank_post(state)
    post_canonical = validate_policy_decide_post(state)

    assert pre_alias.to_dict() == pre_canonical.to_dict()
    assert post_alias.to_dict() == post_canonical.to_dict()


def test_legacy_answer_alias_forwards_with_deprecation_warning() -> None:
    state = _base_state()

    with pytest.warns(DeprecationWarning, match="validate_answer_post"):
        alias_result = validate_answer_post(state)
    canonical_result = validate_answer_commit_post(state)

    assert alias_result.to_dict() == canonical_result.to_dict()


def test_validate_answer_commit_post_accepts_clarify_answer_with_allow_alignment() -> None:
    state = replace(
        _base_state(),
        final_answer=CLARIFY_ANSWER,
        invariant_decisions={
            "answer_contract_valid": True,
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
            "final_alignment_decision": "allow",
        },
    )

    result = validate_answer_commit_post(state)

    assert "alignment_decision_consistent" not in result.failures


def test_validate_answer_commit_post_allows_fallback_alignment_for_non_exempt_answer() -> None:
    state = replace(
        _base_state(),
        final_answer="From memory, I found: release prep requires changelog review.",
        invariant_decisions={
            "answer_contract_valid": True,
            "answer_mode": "memory-grounded",
            "fallback_action": "ANSWER_FROM_MEMORY",
        },
        alignment_decision={
            "dimensions": {
                "factual_grounding_reliability": 0.4,
                "safety_compliance_strictness": 1.0,
                "response_utility": 0.65,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "fallback",
        },
    )

    result = validate_answer_commit_post(state)

    assert "alignment_decision_consistent" not in result.failures
