from __future__ import annotations

from testbot.observability.turn_debug_payload import (
    build_debug_turn_payload,
    format_debug_turn_trace_payload,
    validate_debug_turn_payload_schema,
)
from testbot.pipeline_state import PipelineState


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
