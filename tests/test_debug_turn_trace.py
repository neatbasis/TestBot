from __future__ import annotations

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import _format_debug_turn_trace


def test_format_debug_turn_trace_reports_ambiguous_memory_blocker_reason() -> None:
    state = PipelineState(
        user_input="tell me about ontology",
        rewritten_query="ontology user memory",
        confidence_decision={"context_confident": False, "ambiguity_detected": True},
        invariant_decisions={"answer_mode": "clarify", "fallback_action": "ASK_CLARIFYING_QUESTION"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="memory_recall", hits=[])

    assert "intent=memory_recall" in trace
    assert "answer_mode=clarify" in trace
    assert "fallback_action=ASK_CLARIFYING_QUESTION" in trace
    assert "reject_code=NO_CITABLE_MEMORY_EVIDENCE" in trace
    assert "partition=retrieval" in trace
    assert "blocker_reason=no memory fragments were retrieved for this request" in trace


def test_format_debug_turn_trace_reports_low_confidence_assist_reason() -> None:
    state = PipelineState(
        user_input="summarize this",
        rewritten_query="summarize this",
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="non_memory", hits=[])

    assert "answer_mode=assist" in trace
    assert "fallback_action=OFFER_CAPABILITY_ALTERNATIVES" in trace
    assert "retrieval_branch=memory_retrieval" in trace
    assert "reject_code=CONTEXT_CONF_BELOW_THRESHOLD" in trace
    assert "partition=rerank" in trace
    assert "top1=0.000>0.000" in trace
    assert "context_conf=1.000<1.000" in trace
    assert "margin=0.000>0.000" in trace
    assert "nearest_failure=context_confident_gate:+0.000" in trace
    assert "blocker_reason=retrieved memory fragments were low-confidence for a direct answer" in trace


def test_format_debug_turn_trace_reports_contract_rejection_assist_reason() -> None:
    state = PipelineState(
        user_input="summarize this",
        rewritten_query="summarize this",
        confidence_decision={"context_confident": True, "ambiguity_detected": False},
        invariant_decisions={
            "answer_mode": "assist",
            "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
            "answer_contract_valid": False,
            "general_knowledge_contract_valid": True,
        },
    )

    trace = _format_debug_turn_trace(
        state=state,
        intent_label="memory_recall",
        hits=[Document(page_content="fragment", metadata={"doc_id": "doc-1"})],
    )

    assert "answer_mode=assist" in trace
    assert "context_confident=True" in trace
    assert "top1=0.000>0.000" in trace
    assert "context_conf=1.000>1.000" in trace
    assert "margin=0.000>0.000" in trace
    assert "nearest_failure=answer_contract_gate:+1.000" in trace
    assert "reject_code=ANSWER_CONTRACT_GROUNDING_FAIL" in trace
    assert "partition=contract" in trace
    assert "blocker_reason=answer-contract rejection: draft did not satisfy grounding/citation requirements" in trace


def test_format_debug_turn_trace_reports_direct_answer_branch() -> None:
    state = PipelineState(
        user_input="what is ontology",
        rewritten_query="what is ontology",
        confidence_decision={"context_confident": False, "ambiguity_detected": False, "retrieval_branch": "direct_answer"},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="non_memory", hits=[])

    assert "intent=non_memory" in trace
    assert "retrieval_branch=direct_answer" in trace


def test_format_debug_turn_trace_non_memory_no_ambiguity_does_not_report_clarify() -> None:
    state = PipelineState(
        user_input="what is topology",
        rewritten_query="what is topology",
        confidence_decision={"context_confident": False, "ambiguity_detected": False, "retrieval_branch": "direct_answer"},
        invariant_decisions={"answer_mode": "memory-grounded", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="non_memory", hits=[])

    assert "intent=non_memory" in trace
    assert "ambiguity_detected=False" in trace
    assert "answer_mode=clarify" not in trace


def test_format_debug_turn_trace_defaults_to_non_verbose_format() -> None:
    state = PipelineState(
        user_input="what is ontology",
        rewritten_query="what is ontology",
        confidence_decision={"context_confident": False, "ambiguity_detected": False, "retrieval_branch": "direct_answer"},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="non_memory", hits=[])

    assert trace.startswith("[debug] intent=")
    assert "debug.intent" not in trace


def test_format_debug_turn_trace_compact_trace_includes_gate_scalars_when_candidates_present() -> None:
    state = PipelineState(
        user_input="what did I say about ontology",
        rewritten_query="ontology memory",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "retrieval_branch": "memory_retrieval",
            "top_final_score_min": 0.9,
            "min_margin_to_second": 0.05,
            "scored_candidates": [{"final_score": 0.88}, {"final_score": 0.87}],
        },
        invariant_decisions={
            "answer_mode": "assist",
            "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
        },
    )

    trace = _format_debug_turn_trace(state=state, intent_label="memory_recall", hits=[])

    assert "top1=0.880<0.900" in trace
    assert "context_conf=0.200<1.000" in trace
    assert "margin=0.010<0.050" in trace
    assert "nearest_failure=top_final_score_gate:+0.020" in trace


def test_format_debug_turn_trace_verbose_opt_in_emits_json_payload() -> None:
    state = PipelineState(
        user_input="what is ontology",
        rewritten_query="what is ontology",
        confidence_decision={"context_confident": False, "ambiguity_detected": False, "retrieval_branch": "direct_answer"},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )

    trace = _format_debug_turn_trace(state=state, intent_label="non_memory", hits=[], verbose=True)

    assert trace.startswith("[debug] {")
    assert '"debug.intent"' in trace
