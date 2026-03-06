from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

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
            text_clarification_available=True,
            satellite_ask_available=False,
        ),
        clock=None,
    )

    assert "interaction:" in answer_state.final_answer
    assert "Clarification/disambiguation: available" in answer_state.final_answer
    assert "text clarification still available in CLI" in answer_state.final_answer
    assert "interactive satellite ask flow unavailable in CLI mode" in answer_state.final_answer
    assert "Satellite ask loop: unavailable" in answer_state.final_answer
    assert "Home Assistant satellite actions: unavailable" in answer_state.final_answer
    assert "can continue in cli mode (CLI fallback is active)" in answer_state.final_answer
    assert "Debug visibility: disabled (set TESTBOT_DEBUG=1 to enable)" in answer_state.final_answer
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
            text_clarification_available=True,
            satellite_ask_available=True,
        ),
        clock=None,
    )

    assert "Home Assistant satellite actions: available" in answer_state.final_answer
    assert "can use satellite speak/start-conversation actions" in answer_state.final_answer
    assert "Clarification/disambiguation: available" in answer_state.final_answer
    assert "Satellite ask loop: available" in answer_state.final_answer
    assert "Debug visibility: enabled (TESTBOT_DEBUG=1)" in answer_state.final_answer
    assert "Memory recall: available" in answer_state.final_answer
    assert answer_state.draft_answer == ""


def test_stage_answer_capabilities_help_reports_unavailable_when_no_clarification_path() -> None:
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
            text_clarification_available=False,
            satellite_ask_available=False,
        ),
        clock=None,
    )

    assert "Clarification/disambiguation: unavailable" in answer_state.final_answer
    assert "no clarification path is active in the current runtime" in answer_state.final_answer
    assert "interactive satellite ask flow unavailable" in answer_state.final_answer


def test_debug_flag_does_not_change_non_capabilities_fallback_answer() -> None:
    state = PipelineState(
        user_input="what did I say about ontology",
        confidence_decision={"context_confident": False, "ambiguity_detected": True},
    )
    hits = [
        Document(
            page_content=(
                "type: assistant_utterance\n"
                "ts: 2026-03-06T16:58:55.519389+00:00\n"
                "speaker: assistant\n"
                "channel: cli"
            ),
            metadata={"type": "assistant_utterance", "doc_id": "assist-1"},
            id="assist-1",
        )
    ]

    disabled_answer = stage_answer(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=hits,
        capability_status="ask_unavailable",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=False,
            effective_mode="cli",
            requested_mode="cli",
            daemon_mode=False,
            fallback_reason=None,
            memory_backend="in_memory",
            debug_enabled=False,
            text_clarification_available=True,
            satellite_ask_available=False,
        ),
        clock=None,
    )

    enabled_answer = stage_answer(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=hits,
        capability_status="ask_unavailable",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=False,
            effective_mode="cli",
            requested_mode="cli",
            daemon_mode=False,
            fallback_reason=None,
            memory_backend="in_memory",
            debug_enabled=True,
            text_clarification_available=True,
            satellite_ask_available=False,
        ),
        clock=None,
    )

    assert disabled_answer.final_answer == enabled_answer.final_answer
    assert enabled_answer.final_answer.startswith("I found related memory fragments (")
