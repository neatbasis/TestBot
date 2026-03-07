from __future__ import annotations

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import _build_debug_turn_payload


def _policy_for(*, intent: str, answer_mode: str, fallback_action: str, context_confident: bool, ambiguity: bool, hit_count: int = 0, answer_contract_valid: bool = True, general_knowledge_contract_valid: bool = True) -> dict[str, object]:
    state = PipelineState(
        user_input="u",
        rewritten_query="u",
        classified_intent=intent,
        resolved_intent=intent,
        confidence_decision={
            "context_confident": context_confident,
            "ambiguity_detected": ambiguity,
            "top_final_score_min": 1.0,
            "min_margin_to_second": 1.0,
            "scored_candidates": [{"final_score": 0.2}, {"final_score": 0.1}],
        },
        invariant_decisions={
            "answer_mode": answer_mode,
            "fallback_action": fallback_action,
            "answer_contract_valid": answer_contract_valid,
            "general_knowledge_contract_valid": general_knowledge_contract_valid,
        },
    )
    hits = [] if hit_count == 0 else [Document(page_content="x", metadata={"doc_id": "d"})] * hit_count
    payload = _build_debug_turn_payload(state=state, intent_label=intent, hits=hits)
    return payload["debug.policy"]


def test_reject_taxonomy_code_is_deterministic_for_low_confidence_assist() -> None:
    first = _policy_for(
        intent="memory_recall",
        answer_mode="assist",
        fallback_action="OFFER_CAPABILITY_ALTERNATIVES",
        context_confident=False,
        ambiguity=False,
    )
    second = _policy_for(
        intent="memory_recall",
        answer_mode="assist",
        fallback_action="OFFER_CAPABILITY_ALTERNATIVES",
        context_confident=False,
        ambiguity=False,
    )

    assert first["reject_code"] == "CONTEXT_CONF_BELOW_THRESHOLD"
    assert first["partition"] == "rerank"
    assert first["reject_code"] == second["reject_code"]
    assert first["partition"] == second["partition"]


def test_reject_taxonomy_temporal_unresolved_for_time_query_unknown() -> None:
    policy = _policy_for(
        intent="time_query",
        answer_mode="dont-know",
        fallback_action="ANSWER_UNKNOWN",
        context_confident=False,
        ambiguity=False,
    )

    assert policy["reject_code"] == "TEMPORAL_REFERENCE_UNRESOLVED"
    assert policy["partition"] == "temporal"


def test_reject_taxonomy_backward_compatible_blocker_reason_field() -> None:
    policy = _policy_for(
        intent="memory_recall",
        answer_mode="assist",
        fallback_action="OFFER_CAPABILITY_ALTERNATIVES",
        context_confident=True,
        ambiguity=False,
        hit_count=1,
        answer_contract_valid=False,
    )

    assert policy["reject_code"] == "ANSWER_CONTRACT_GROUNDING_FAIL"
    assert policy["reason"] == "answer-contract rejection: draft did not satisfy grounding/citation requirements"
    assert policy["blocker_reason"] == policy["reason"]
