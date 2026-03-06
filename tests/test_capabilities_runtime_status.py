from __future__ import annotations

from collections import deque

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import (
    _print_startup_status,
    build_capability_snapshot,
    stage_answer,
)


class _FailIfInvokedLLM:
    def invoke(self, _msgs):  # pragma: no cover - should never be reached
        raise AssertionError("LLM should not run for capabilities-help intent")


def _base_runtime() -> dict[str, object]:
    return {
        "ha_api_url": "http://localhost:8123",
        "ha_api_secret": "",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text",
        "memory_store_backend": "in_memory",
    }


def _capabilities_help_answer(snapshot) -> str:
    state = PipelineState(
        user_input="what can you do",
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )
    answer_state = stage_answer(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=snapshot.runtime_capability_status,
        clock=None,
    )
    return answer_state.final_answer


def test_shared_snapshot_keeps_cli_fallback_truth_consistent(monkeypatch, capsys) -> None:
    runtime = _base_runtime()
    monkeypatch.setattr("testbot.sat_chatbot_memory_v2._ha_connection_error", lambda *_args: "Missing HA_API_SECRET")
    monkeypatch.setattr("testbot.sat_chatbot_memory_v2._ollama_connection_error", lambda *_args: None)

    snapshot = build_capability_snapshot(requested_mode="auto", daemon_mode=False, runtime=runtime)
    _print_startup_status(snapshot=snapshot)

    startup_output = capsys.readouterr().out
    help_answer = _capabilities_help_answer(snapshot)

    assert "Selected mode: cli" in startup_output
    assert "Home Assistant: unavailable" in startup_output
    assert "Install warning [YELLOW]" in startup_output

    assert "Runtime mode: requested=auto, effective=cli" in help_answer
    assert "Home Assistant satellite actions: unavailable" in help_answer
    assert "CLI fallback is active" in help_answer
    assert "Clarification/disambiguation: available" in help_answer
    assert "text clarification still available in CLI" in help_answer
    assert "interactive satellite ask flow unavailable in CLI mode" in help_answer


def test_shared_snapshot_keeps_satellite_truth_consistent(monkeypatch, capsys) -> None:
    runtime = _base_runtime()
    runtime["ha_api_secret"] = "top-secret"
    monkeypatch.setattr("testbot.sat_chatbot_memory_v2._ha_connection_error", lambda *_args: None)
    monkeypatch.setattr("testbot.sat_chatbot_memory_v2._ollama_connection_error", lambda *_args: None)

    snapshot = build_capability_snapshot(requested_mode="satellite", daemon_mode=False, runtime=runtime)
    _print_startup_status(snapshot=snapshot)

    startup_output = capsys.readouterr().out
    help_answer = _capabilities_help_answer(snapshot)

    assert "Selected mode: satellite" in startup_output
    assert "Home Assistant: available" in startup_output
    assert "Install warning [GREEN]" in startup_output

    assert "Runtime mode: requested=satellite, effective=satellite" in help_answer
    assert "Home Assistant satellite actions: available" in help_answer
    assert "can use satellite speak/start-conversation actions" in help_answer
