from __future__ import annotations

from testbot.observability.turn_debug_payload import (
    build_debug_turn_payload,
    format_debug_turn_trace_payload,
    validate_debug_turn_payload_schema,
)
from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import (
    build_debug_turn_payload as build_debug_turn_payload_compat,
    format_debug_turn_trace_payload as format_debug_turn_trace_payload_compat,
)


def _sample_state() -> PipelineState:
    return PipelineState(
        user_input="what did I say",
        rewritten_query="what did i say",
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


def test_turn_debug_payload_module_validates_and_formats_compact_trace() -> None:
    payload = build_debug_turn_payload(state=_sample_state(), intent_label="memory_recall", hits=[])

    validate_debug_turn_payload_schema(payload)
    trace = format_debug_turn_trace_payload(payload=payload, verbose=False)

    assert trace.startswith("[debug] intent=memory_recall;")
    assert "top1=" in trace
    assert "margin=" in trace


def test_sat_chatbot_debug_payload_compatibility_wrappers_match_observability_module() -> None:
    module_payload = build_debug_turn_payload(state=_sample_state(), intent_label="memory_recall", hits=[])
    compat_payload = build_debug_turn_payload_compat(state=_sample_state(), intent_label="memory_recall", hits=[])

    assert compat_payload == module_payload
    assert format_debug_turn_trace_payload_compat(payload=compat_payload, verbose=False) == format_debug_turn_trace_payload(
        payload=module_payload,
        verbose=False,
    )
