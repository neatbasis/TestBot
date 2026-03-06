from __future__ import annotations

from collections import deque
import os

import pytest

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import (
    _print_startup_status,
    _read_runtime_env,
    build_capability_snapshot,
    stage_answer,
)


pytestmark = pytest.mark.live_smoke

if os.getenv("TESTBOT_ENABLE_LIVE_SMOKE", "").strip().lower() not in {"1", "true", "yes"}:
    pytest.skip(
        "Set TESTBOT_ENABLE_LIVE_SMOKE=1 to run degraded-mode live_smoke tests",
        allow_module_level=True,
    )


class _FailIfInvokedLLM:
    def invoke(self, _msgs):  # pragma: no cover - should not execute for capabilities-help intent
        raise AssertionError("LLM should not run for capabilities-help intent")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run degraded-mode live_smoke tests")
    return value


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


@pytest.mark.parametrize(
    (
        "scenario_name",
        "ha_endpoint",
        "ha_secret",
        "ha_entity_id",
        "ollama_endpoint",
        "expected_selected_mode",
        "expected_ha_flag",
        "expected_ollama_flag",
        "expected_help_ha_line",
        "expected_help_guidance",
    ),
    [
        (
            "ha_unavailable_ollama_available",
            "http://127.0.0.1:9",
            "fake-token",
            "assist_satellite.kitchen",
            "LIVE_OLLAMA",
            "cli",
            False,
            True,
            "Home Assistant satellite actions: unavailable",
            "CLI fallback is active",
        ),
        (
            "ha_available_ollama_unavailable",
            "LIVE_HA",
            "LIVE_HA",
            "LIVE_HA",
            "http://127.0.0.1:1",
            "unavailable",
            True,
            False,
            "Home Assistant satellite actions: degraded",
            "current mode is CLI",
        ),
        (
            "both_unavailable",
            "http://127.0.0.1:9",
            "fake-token",
            "assist_satellite.kitchen",
            "http://127.0.0.1:1",
            "unavailable",
            False,
            False,
            "Home Assistant satellite actions: unavailable",
            "CLI fallback is active",
        ),
    ],
)
def test_live_smoke_degraded_modes_runtime_contracts(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scenario_name: str,
    ha_endpoint: str,
    ha_secret: str,
    ha_entity_id: str,
    ollama_endpoint: str,
    expected_selected_mode: str,
    expected_ha_flag: bool,
    expected_ollama_flag: bool,
    expected_help_ha_line: str,
    expected_help_guidance: str,
) -> None:
    if ha_endpoint == "LIVE_HA":
        ha_endpoint = _require_env("HA_API_URL")
        ha_secret = _require_env("HA_API_SECRET")
        ha_entity_id = _require_env("HA_SATELLITE_ENTITY_ID")

    if ollama_endpoint == "LIVE_OLLAMA":
        ollama_endpoint = _require_env("OLLAMA_BASE_URL")
        _require_env("OLLAMA_MODEL")
        _require_env("OLLAMA_EMBEDDING_MODEL")

    monkeypatch.setenv("HA_API_URL", ha_endpoint)
    monkeypatch.setenv("HA_API_SECRET", ha_secret)
    monkeypatch.setenv("HA_SATELLITE_ENTITY_ID", ha_entity_id)
    monkeypatch.setenv("OLLAMA_BASE_URL", ollama_endpoint)
    monkeypatch.setenv("MEMORY_STORE_MODE", "in_memory")

    runtime = _read_runtime_env()
    snapshot = build_capability_snapshot(requested_mode="auto", daemon_mode=False, runtime=runtime)

    _print_startup_status(snapshot=snapshot)
    startup_output = capsys.readouterr().out
    help_answer = _capabilities_help_answer(snapshot)

    assert f"Selected mode: {expected_selected_mode}" in startup_output, scenario_name
    assert snapshot.runtime_capability_status.ha_available is expected_ha_flag, scenario_name
    assert snapshot.runtime_capability_status.ollama_available is expected_ollama_flag, scenario_name

    assert expected_help_ha_line in help_answer, scenario_name
    assert expected_help_guidance in help_answer, scenario_name
    assert (
        f"Runtime mode: requested=auto, effective={expected_selected_mode}" in help_answer
    ), scenario_name
