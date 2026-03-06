from __future__ import annotations

from collections import deque

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import RuntimeCapabilityStatus, stage_answer


class _FailIfInvokedLLM:
    def invoke(self, _msgs):  # pragma: no cover - should never be reached
        raise AssertionError("LLM should not run for capabilities-help intent")


def _base_state() -> PipelineState:
    return PipelineState(
        user_input="what can you do",
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )


def test_stage_answer_capabilities_help_reflects_ha_unavailable_cli_fallback() -> None:
    answer_state = stage_answer(
        _FailIfInvokedLLM(),
        _base_state(),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=False,
            effective_mode="cli",
            requested_mode="auto",
            daemon_mode=False,
            fallback_reason="satellite connection is unavailable",
            memory_backend="in_memory",
            debug_enabled=False,
        ),
        clock=None,
    )

    assert "Home Assistant actions: unavailable" in answer_state.final_answer
    assert "can continue in cli mode (CLI fallback is active)" in answer_state.final_answer
    assert "Ask/disambiguation flow: degraded" in answer_state.final_answer
    assert "Debug visibility: unavailable" in answer_state.final_answer
    assert answer_state.draft_answer == ""


def test_stage_answer_capabilities_help_reflects_ha_satellite_available() -> None:
    answer_state = stage_answer(
        _FailIfInvokedLLM(),
        _base_state(),
        chat_history=deque(),
        hits=[],
        capability_status="ask_available",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=True,
            effective_mode="satellite",
            requested_mode="satellite",
            daemon_mode=False,
            fallback_reason=None,
            memory_backend="elasticsearch",
            debug_enabled=True,
        ),
        clock=None,
    )

    assert "Home Assistant actions: available" in answer_state.final_answer
    assert "can use satellite ask/speak actions" in answer_state.final_answer
    assert "Ask/disambiguation flow: available" in answer_state.final_answer
    assert "Debug visibility: available" in answer_state.final_answer
    assert "Memory recall: available" in answer_state.final_answer
    assert answer_state.draft_answer == ""
