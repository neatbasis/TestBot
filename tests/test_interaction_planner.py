from __future__ import annotations

from collections import deque
from types import SimpleNamespace

from testbot.adapters.ask_gateway import AskTurnInput, STOP_DECISION_ID
from testbot.entrypoints import sat_runtime_modes
from testbot.interaction_planner import (
    ChannelContext,
    InteractionPlanResult,
    InteractionShape,
    InteractionStandardsProfile,
    NeedProfile,
    plan_interaction,
)


def test_plan_interaction_returns_stable_id_and_optional_rationale() -> None:
    result = plan_interaction(
        need_profile=NeedProfile(task_intent_requirements="memory_grounded_turn"),
        channel_context=ChannelContext(channel_id="cli", supports_satellite_ask=False),
        interaction_standards_profile=InteractionStandardsProfile(
            profile_id="runtime-mode-v1",
            deterministic_rationale=True,
        ),
    )

    assert result.recommended_shape is InteractionShape.CLI_TEXT_LOOP
    assert result.stable_id == "runtime-mode-v1:cli_text_loop"
    assert result.rationale == (
        "intent=memory_grounded_turn;"
        "channel=cli;"
        "supports_satellite_ask=False;"
        "shape=cli_text_loop"
    )


def test_plan_interaction_prefers_satellite_shape_when_supported() -> None:
    result = plan_interaction(
        need_profile=NeedProfile(task_intent_requirements="memory_grounded_turn"),
        channel_context=ChannelContext(channel_id="satellite", supports_satellite_ask=True),
        interaction_standards_profile=InteractionStandardsProfile(profile_id="runtime-mode-v1"),
    )

    assert result.recommended_shape is InteractionShape.SATELLITE_VOICE_LOOP
    assert result.stable_id == "runtime-mode-v1:satellite_voice_loop"


def test_run_satellite_mode_uses_planner_shape_for_prompt_and_capability(monkeypatch) -> None:
    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    observed: dict[str, object] = {"question": None, "capability_status": None}

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())
    monkeypatch.setattr(
        sat_runtime_modes,
        "plan_interaction",
        lambda **_kwargs: InteractionPlanResult(
            recommended_shape=InteractionShape.CLI_TEXT_LOOP,
            stable_id="runtime-mode-v1:cli_text_loop",
        ),
    )

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_satellite_turn_input(self, *, question: str, timeout_s: float = 60.0) -> AskTurnInput:
            observed["question"] = question
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)

    def _fake_run_chat_loop(*, capability_status, read_user_utterance, **_kwargs):
        observed["capability_status"] = capability_status
        assert read_user_utterance() == "stop"

    sat_runtime_modes.run_satellite_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.1,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert observed["question"] == "Share one memory-grounded question in text form."
    assert observed["capability_status"] == "ask_unavailable"
