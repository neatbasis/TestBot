from __future__ import annotations

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import _build_debug_turn_payload, _format_debug_turn_trace


REQUIRED_DEBUG_KEYS = {
    "debug.intent",
    "debug.rewrite",
    "debug.retrieval",
    "debug.rerank",
    "debug.confidence",
    "debug.observation",
    "debug.contract",
    "debug.policy",
}


def _assert_gate_shape(gate: dict[str, object]) -> None:
    assert set(gate.keys()) == {"passed", "score", "threshold", "margin"}


def test_structured_debug_payload_memory_recall_contains_stage_sections() -> None:
    state = PipelineState(
        user_input="what did I say about ontology",
        rewritten_query="ontology memory",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
            "retrieval_branch": "memory_retrieval",
            "top_final_score_min": 0.9,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.71}, {"final_score": 0.69}],
        },
        invariant_decisions={"answer_mode": "clarify", "fallback_action": "ASK_CLARIFYING_QUESTION"},
    )

    payload = _build_debug_turn_payload(state=state, intent_label="memory_recall", hits=[])

    assert set(payload.keys()) == REQUIRED_DEBUG_KEYS
    _assert_gate_shape(payload["debug.rerank"]["top_final_score_gate"])
    _assert_gate_shape(payload["debug.rerank"]["margin_gate"])
    _assert_gate_shape(payload["debug.rerank"]["ambiguity_gate"])
    _assert_gate_shape(payload["debug.confidence"]["context_confident_gate"])


def test_structured_debug_payload_knowledge_includes_contract_gate_scalars() -> None:
    state = PipelineState(
        user_input="what is ontology",
        rewritten_query="what is ontology",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "retrieval_branch": "direct_answer",
            "top_final_score_min": 0.8,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.88}, {"final_score": 0.6}],
        },
        invariant_decisions={
            "answer_mode": "assist",
            "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
        },
    )

    payload = _build_debug_turn_payload(state=state, intent_label="knowledge_question", hits=[])

    _assert_gate_shape(payload["debug.contract"]["answer_contract_gate"])
    _assert_gate_shape(payload["debug.contract"]["general_knowledge_contract_gate"])


def test_structured_debug_payload_policy_reject_signal_shape_and_legacy_reason() -> None:
    state = PipelineState(
        user_input="summarize this",
        rewritten_query="summarize this",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES"},
    )

    payload = _build_debug_turn_payload(state=state, intent_label="memory_recall", hits=[])

    policy = payload["debug.policy"]
    assert set(policy.keys()) >= {
        "answer_mode",
        "fallback_action",
        "reject_code",
        "partition",
        "score",
        "threshold",
        "margin",
        "reason",
        "blocker_reason",
    }
    assert policy["reject_code"] == "CONTEXT_CONF_BELOW_THRESHOLD"
    assert policy["partition"] == "rerank"
    assert policy["reason"] == policy["blocker_reason"]
    assert policy["chosen_action"] == "OFFER_CAPABILITY_ALTERNATIVES"
    assert isinstance(policy["considered_alternatives"], list)
    assert any(option["status"] == "rejected" for option in policy["considered_alternatives"])
    assert "thresholds" in policy["decision_rationale"]


def test_structured_debug_payload_observation_includes_candidate_evidence_details() -> None:
    state = PipelineState(
        user_input="what did I say about that yesterday",
        rewritten_query="ontology update yesterday",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        last_user_message_ts="2026-03-01T08:00:00Z",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
            "anaphora_detected": True,
            "anaphora_target": "that",
            "time_window": "yesterday",
            "window_start": "2026-02-29T00:00:00Z",
            "window_end": "2026-02-29T23:59:59Z",
            "top_final_score_min": 0.85,
            "min_margin_to_second": 0.1,
            "scored_candidates": [{"final_score": 0.61}, {"final_score": 0.6}],
        },
        invariant_decisions={"answer_mode": "clarify", "fallback_action": "ASK_CLARIFYING_QUESTION"},
    )

    payload = _build_debug_turn_payload(
        state=state,
        intent_label="memory_recall",
        hits=[],
    )

    observation = payload["debug.observation"]["candidate_evidence"]
    assert set(observation.keys()) == {"retrieved_docs", "score_components", "time_windows", "ambiguity_state"}
    assert observation["score_components"]["top_gate_threshold"] == 0.85
    assert observation["time_windows"]["query_time_window"] == "yesterday"
    assert observation["ambiguity_state"]["anaphora_detected"] is True


def test_structured_debug_payload_temporal_query_is_emitted_in_verbose_trace() -> None:
    state = PipelineState(
        user_input="what is tomorrow",
        rewritten_query="what is tomorrow",
        classified_intent="time_query",
        resolved_intent="time_query",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "retrieval_branch": "direct_answer",
        },
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="time_query", hits=[], verbose=True)

    assert trace.startswith("[debug] {")
    for key in REQUIRED_DEBUG_KEYS:
        assert key in trace
