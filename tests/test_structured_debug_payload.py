from __future__ import annotations

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import _build_debug_turn_payload, _format_debug_turn_trace, _format_debug_turn_trace_payload


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
    assert payload["debug.contract"]["general_knowledge_contract_applicability"] == "applicable"
    assert payload["debug.contract"]["general_knowledge_contract_failed_when_applicable"] is False




def test_structured_debug_payload_memory_recall_emits_numeric_intent_and_retrieval_telemetry() -> None:
    state = PipelineState(
        user_input="what did I say about ontology",
        rewritten_query="ontology memory",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        confidence_decision={
            "intent_predicted": "memory_recall",
            "intent_classifier_confidence": 0.95,
            "intent_classifier_threshold": 0.75,
            "retrieval_branch": "memory_retrieval",
            "retrieval_candidates_considered": 18,
            "retrieval_returned_top_k": 12,
            "retrieval_threshold": 0.0,
            "context_confident": False,
            "ambiguity_detected": True,
            "top_final_score_min": 0.9,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.71}, {"final_score": 0.69}],
        },
        invariant_decisions={"answer_mode": "clarify", "fallback_action": "ASK_CLARIFYING_QUESTION"},
    )

    payload = _build_debug_turn_payload(state=state, intent_label="memory_recall", hits=[])

    assert payload["debug.intent"]["predicted"] == "memory_recall"
    assert isinstance(payload["debug.intent"]["confidence"], float)
    assert isinstance(payload["debug.intent"]["threshold"], float)
    assert payload["debug.retrieval"]["branch"] == "memory_retrieval"
    assert isinstance(payload["debug.retrieval"]["candidates_considered"], float)
    assert isinstance(payload["debug.retrieval"]["returned_top_k"], float)
    assert isinstance(payload["debug.retrieval"]["threshold"], float)


def test_structured_debug_payload_knowledge_question_emits_numeric_intent_and_retrieval_telemetry() -> None:
    state = PipelineState(
        user_input="what is ontology",
        rewritten_query="what is ontology",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
        confidence_decision={
            "intent_predicted": "knowledge_question",
            "intent_classifier_confidence": 0.82,
            "intent_classifier_threshold": 0.75,
            "retrieval_branch": "direct_answer",
            "retrieval_candidates_considered": 0,
            "retrieval_returned_top_k": 0,
            "retrieval_threshold": 0.0,
            "context_confident": True,
            "ambiguity_detected": False,
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

    assert payload["debug.intent"]["predicted"] == "knowledge_question"
    assert isinstance(payload["debug.intent"]["confidence"], float)
    assert isinstance(payload["debug.intent"]["threshold"], float)
    assert payload["debug.retrieval"]["branch"] == "direct_answer"
    assert isinstance(payload["debug.retrieval"]["candidates_considered"], float)
    assert isinstance(payload["debug.retrieval"]["returned_top_k"], float)
    assert isinstance(payload["debug.retrieval"]["threshold"], float)

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
            "anchor_candidates": [{"doc_id": "d1", "ts": "2026-02-29T12:00:00Z", "confidence": 0.7}],
            "selected_anchor_doc_id": "d1",
            "selected_anchor_ts": "2026-02-29T12:00:00Z",
            "computed_delta_raw_seconds": 3600,
            "computed_delta_humanized": "1 hours ago",
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
    assert isinstance(observation["score_components"]["candidate_score_decomposition"], list)
    assert observation["time_windows"]["query_time_window"] == "yesterday"
    assert observation["ambiguity_state"]["anaphora_detected"] is True
    assert observation["ambiguity_state"]["selected_anchor_doc_id"] == "d1"



def test_structured_debug_payload_rejected_turn_has_nearest_gate_and_counterfactuals() -> None:
    state = PipelineState(
        user_input="what did I say about that",
        rewritten_query="what did I say about that",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "top_final_score_min": 0.9,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.88}, {"final_score": 0.87}],
        },
        invariant_decisions={
            "answer_mode": "assist",
            "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
            "answer_contract_valid": False,
            "general_knowledge_contract_valid": True,
        },
    )

    payload = _build_debug_turn_payload(state=state, intent_label="memory_recall", hits=[])

    policy = payload["debug.policy"]
    assert policy["rejected_turn"] is True
    assert policy["nearest_failure_gate"] == {
        "gate": "top_final_score_gate",
        "current": 0.88,
        "required": 0.9,
        "margin_to_pass": 0.02,
    }
    assert policy["counterfactuals"]["top_candidate_pass_thresholds"] == {
        "top_final_score_min": 0.9,
        "min_margin_to_second": 0.05,
        "context_score_target": 1.0,
    }
    assert policy["counterfactuals"]["alternate_routing_policy_checks"] == {
        "ask_clarifying_question_passes": False,
        "route_to_ask_passes": False,
    }
    assert policy["counterfactuals"]["nearest_pass_frontier"] == [
        {
            "family": "confidence",
            "gate": "context_confident_gate",
            "current": 0.2,
            "required": 1.0,
            "delta_to_pass": 0.8,
        },
        {
            "family": "contract",
            "gate": "answer_contract_gate",
            "current": 0.0,
            "required": 1.0,
            "delta_to_pass": 1.0,
        },
        {
            "family": "rerank",
            "gate": "top_final_score_gate",
            "current": 0.88,
            "required": 0.9,
            "delta_to_pass": 0.02,
        },
    ]
    assert policy["counterfactuals"]["dominant_contributors"] == [
        {"component": "provenance_citation_factor", "current": 0.0, "delta_to_ideal": 1.0},
        {"component": "semantic_similarity", "current": 0.0, "delta_to_ideal": 1.0},
    ]



def test_structured_debug_payload_temporal_rejection_includes_temporal_frontier_and_contributors() -> None:
    state = PipelineState(
        user_input="what happened then",
        rewritten_query="what happened then",
        classified_intent="time_query",
        resolved_intent="time_query",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "anaphora_detected": True,
            "top_final_score_min": 0.8,
            "min_margin_to_second": 0.05,
            "scored_candidates": [
                {
                    "final_score": 0.4,
                    "semantic_similarity": 0.92,
                    "time_decay_freshness": 0.18,
                    "type_prior": 0.85,
                    "provenance_citation_factor": 0.94,
                },
                {"final_score": 0.35},
            ],
        },
        invariant_decisions={"answer_mode": "dont-know", "fallback_action": "ANSWER_UNKNOWN"},
    )

    payload = _build_debug_turn_payload(state=state, intent_label="time_query", hits=[])

    counterfactuals = payload["debug.policy"]["counterfactuals"]
    assert counterfactuals["nearest_pass_frontier"] == [
        {"family": "confidence", "gate": "context_confident_gate", "current": 0.5, "required": 1.0, "delta_to_pass": 0.5},
        {"family": "rerank", "gate": "top_final_score_gate", "current": 0.4, "required": 0.8, "delta_to_pass": 0.4},
        {"family": "temporal", "gate": "temporal_reference_gate", "current": 0.0, "required": 1.0, "delta_to_pass": 1.0},
    ]
    assert counterfactuals["dominant_contributors"] == [
        {"component": "time_decay_freshness", "current": 0.18, "delta_to_ideal": 0.82},
        {"component": "type_prior", "current": 0.85, "delta_to_ideal": 0.15},
    ]


def test_structured_debug_payload_contract_rejection_frontier_focuses_contract_gate() -> None:
    state = PipelineState(
        user_input="summarize the release notes",
        rewritten_query="summarize the release notes",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "top_final_score_min": 0.75,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.92}, {"final_score": 0.7}],
        },
        invariant_decisions={
            "answer_mode": "assist",
            "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
            "answer_contract_valid": False,
            "general_knowledge_contract_valid": True,
        },
    )

    payload = _build_debug_turn_payload(state=state, intent_label="knowledge_question", hits=[])

    assert payload["debug.policy"]["counterfactuals"]["nearest_pass_frontier"] == [
        {"family": "contract", "gate": "answer_contract_gate", "current": 0.0, "required": 1.0, "delta_to_pass": 1.0}
    ]

def test_structured_debug_payload_non_rejected_turn_has_no_nearest_failure_gate() -> None:
    state = PipelineState(
        user_input="what time is it",
        rewritten_query="what time is it",
        classified_intent="time_query",
        resolved_intent="time_query",
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "top_final_score_min": 0.8,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.9}, {"final_score": 0.7}],
        },
        invariant_decisions={
            "answer_mode": "memory-grounded",
            "fallback_action": "ANSWER_TIME",
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
        },
    )

    payload = _build_debug_turn_payload(state=state, intent_label="time_query", hits=[])

    policy = payload["debug.policy"]
    assert policy["rejected_turn"] is False
    assert policy["nearest_failure_gate"] is None

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


def test_structured_debug_payload_policy_chosen_action_matches_fallback_action_authority() -> None:
    state = PipelineState(
        user_input="what did I say about release prep",
        rewritten_query="release prep",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
            "retrieval_branch": "memory_retrieval",
            "top_final_score_min": 0.8,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.92}, {"final_score": 0.74}],
        },
        invariant_decisions={
            "answer_mode": "memory-grounded",
            "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
            "answer_policy_rationale": {"authority": "decision_object", "decision_class": "answer_from_memory"},
        },
    )

    payload = _build_debug_turn_payload(state=state, intent_label="memory_recall", hits=[])

    assert payload["debug.policy"]["fallback_action"] == "ANSWER_GENERAL_KNOWLEDGE"
    assert payload["debug.policy"]["chosen_action"] == payload["debug.policy"]["fallback_action"]


def test_debug_turn_payload_schema_drift_fails_loudly_in_formatter() -> None:
    state = PipelineState(
        user_input="what is ontology",
        rewritten_query="what is ontology",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )

    payload = _build_debug_turn_payload(state=state, intent_label="knowledge_question", hits=[])
    payload.pop("debug.policy")

    try:
        _format_debug_turn_trace_payload(payload=payload, verbose=False)
    except ValueError as exc:
        assert "schema drift" in str(exc)
    else:
        raise AssertionError("expected ValueError for debug payload schema drift")


def test_debug_payload_generation_is_observational_only_for_pipeline_state() -> None:
    state = PipelineState(
        user_input="what did I say",
        rewritten_query="what did I say",
        classified_intent="memory_recall",
        resolved_intent="memory_recall",
        confidence_decision={"context_confident": False, "ambiguity_detected": True},
        invariant_decisions={"answer_mode": "clarify", "fallback_action": "ASK_CLARIFYING_QUESTION"},
    )
    before_confidence = state.confidence_decision.to_dict()
    before_invariant = state.invariant_decisions.to_dict()

    _build_debug_turn_payload(state=state, intent_label="memory_recall", hits=[])

    assert state.confidence_decision.to_dict() == before_confidence
    assert state.invariant_decisions.to_dict() == before_invariant


def test_structured_debug_payload_non_applicable_gk_contract_does_not_emit_false_failure() -> None:
    state = PipelineState(
        user_input="help me figure this out",
        rewritten_query="help me figure this out",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "retrieval_branch": "direct_answer",
        },
        invariant_decisions={
            "answer_mode": "assist",
            "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": False,
            "general_knowledge_contract_applicability": "not_applicable",
        },
    )

    payload = _build_debug_turn_payload(state=state, intent_label="knowledge_question", hits=[])

    assert payload["debug.contract"]["general_knowledge_contract_gate"]["passed"] is True
    assert payload["debug.contract"]["general_knowledge_contract_applicability"] == "not_applicable"
    assert payload["debug.contract"]["general_knowledge_contract_failed_when_applicable"] is False


def test_structured_debug_payload_intent_metrics_are_null_when_not_persisted() -> None:
    state = PipelineState(
        user_input="hello",
        rewritten_query="hello",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_UNKNOWN"},
    )

    payload = _build_debug_turn_payload(state=state, intent_label="knowledge_question", hits=[])

    assert payload["debug.intent"]["confidence"] is None
    assert payload["debug.intent"]["threshold"] is None
    assert payload["debug.intent"]["model"] is None
    assert payload["debug.intent"]["version"] is None
