from __future__ import annotations

import importlib.util
import json
import re
from collections import deque
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from testbot.entrypoints import cli, sat_cli
from testbot.entrypoints.runtime_legacy_bridge import read_runtime_env
from testbot.adapters.ask_gateway import AskTurnInput, STOP_DECISION_ID
from testbot.interaction_policy import InteractionPolicyRequest
from testbot.interaction_standards import InteractionRequirements
from testbot.entrypoints import sat_runtime_modes
from testbot.runtime_capability_service import resolve_mode
from testbot.runtime_cli_args import parse_args
from testbot.sat_chatbot_memory_v2 import CLARIFY_ANSWER, resolve_turn_intent
from testbot import sat_chatbot_memory_v2 as runtime
import testbot.runtime_capability_service as runtime_capability_service





def test_sat_runtime_modes_does_not_import_monolith_runtime_for_profile_selection() -> None:
    source = Path(sat_runtime_modes.__file__).read_text()
    assert "from testbot.sat_chatbot_memory_v2" not in source


def test_entrypoints_package_exposes_lazy_main_wrapper_without_eager_sat_cli_import() -> None:
    source = Path("src/testbot/entrypoints/__init__.py").read_text()
    assert "from .sat_cli import main\n" not in source
    assert "def main(" in source
    assert "from .cli import main as cli_main" in source


def test_sat_runtime_modes_does_not_depend_on_runtime_legacy_bridge_symbols() -> None:
    source = Path(sat_runtime_modes.__file__).read_text()
    assert "from testbot.entrypoints.runtime_legacy_bridge import" not in source


def test_runtime_legacy_bridge_warns_on_monolith_compat_usage() -> None:
    with pytest.deprecated_call(match="runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2"):
        read_runtime_env()


def test_runtime_loop_owner_handles_none_input_as_immediate_return(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    poll_calls: list[dict[str, object]] = []
    completion_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        runtime_loop,
        "poll_pending_ingestion_obligations",
        lambda *, runtime, deps: poll_calls.append(runtime),
    )

    def _fake_completion(**kwargs):
        completion_calls.append(kwargs)
        return "", None, False

    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", _fake_completion)

    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-01-01T00:00:00+00:00")),
    )

    assert len(poll_calls) == 1
    assert len(completion_calls) == 1



def test_runtime_loop_owner_handles_stop_command_without_turn_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    sent: list[str] = []
    run_pipeline_called = False

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))

    def _unexpected_pipeline_call(**_kwargs):
        nonlocal run_pipeline_called
        run_pipeline_called = True
        raise AssertionError("pipeline should not run for stop command")

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _unexpected_pipeline_call)

    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=SimpleNamespace(
            runtime_capability_status=SimpleNamespace(debug_enabled=False, debug_verbose=False)
        ),
        read_user_utterance=lambda: " stop ",
        send_assistant_text=sent.append,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-01-01T00:00:00+00:00")),
    )

    assert sent == ["Stopping. Bye."]
    assert run_pipeline_called is False


def test_runtime_loop_sat_say_delegates_to_ha_satellite_output_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    captured: dict[str, object] = {}

    def _fake_send_satellite_output(client, entity_id: str, text: str) -> None:
        captured["client"] = client
        captured["entity_id"] = entity_id
        captured["text"] = text

    monkeypatch.setattr("testbot.entrypoints.runtime_loop.send_satellite_output", _fake_send_satellite_output)
    fake_client = object()
    runtime_loop.sat_say(fake_client, "assist_satellite.kitchen", "hello")

    assert captured == {
        "client": fake_client,
        "entity_id": "assist_satellite.kitchen",
        "text": "hello",
    }


def test_runtime_legacy_bridge_run_chat_loop_delegates_to_runtime_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_legacy_bridge

    runtime_legacy_bridge._LEGACY_RUNTIME_WARNING_EMITTED = False
    captured: dict[str, object] = {}

    def _fake_runtime_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("testbot.entrypoints.runtime_loop.run_chat_loop", _fake_runtime_loop)
    with pytest.deprecated_call(match="runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2"):
        runtime_legacy_bridge.run_chat_loop(
            runtime={},
            llm=object(),
            store=object(),
            chat_history=deque(),
            near_tie_delta=0.3,
            io_channel="satellite",
            capability_status="ok",
            capability_snapshot=object(),
            read_user_utterance=lambda: None,
            send_assistant_text=lambda _text: None,
            clock=object(),
        )

    assert captured["io_channel"] == "satellite"
    assert captured["near_tie_delta"] == 0.3


def test_monolith_run_chat_loop_delegates_to_runtime_loop_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_runtime_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("testbot.entrypoints.runtime_loop.run_chat_loop", _fake_runtime_loop)

    runtime.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.3,
        io_channel="cli",
        capability_status="ok",
        capability_snapshot=object(),
        read_user_utterance=lambda: None,
        send_assistant_text=lambda _text: None,
        clock=object(),
    )

    assert captured["io_channel"] == "cli"
    assert captured["near_tie_delta"] == 0.3


def test_legacy_runtime_main_warns_once_and_delegates_to_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    forwarded: list[list[str] | None] = []

    def _fake_cli_main(argv: list[str] | None = None) -> None:
        forwarded.append(argv)

    monkeypatch.setattr("testbot.entrypoints.cli.main", _fake_cli_main)
    runtime._LEGACY_MAIN_WARNING_EMITTED = False

    with pytest.warns(DeprecationWarning, match=r"testbot\.sat_chatbot_memory_v2\.main\(\.\.\.\)"):
        runtime.main(["--mode", "cli"])
    runtime.main(["--mode", "satellite"])

    assert len(forwarded) == 2
    assert forwarded[0] == ["--mode", "cli"]
    assert forwarded[1] == ["--mode", "satellite"]


def test_cli_uses_runtime_bootstrap_owner_and_limits_legacy_bridge_imports() -> None:
    source = Path(cli.__file__).read_text()
    assert "from testbot.entrypoints.runtime_bootstrap import build_runtime_memory_store, read_runtime_env" in source
    assert "from testbot.entrypoints.runtime_loop import run_chat_loop" in source
    assert "from testbot.adapters.ha_satellite_output import send_satellite_output" in source
    assert "from testbot.entrypoints.runtime_legacy_bridge import" not in source
    assert "from testbot.runtime_capability_service import build_capability_snapshot" in source
    assert "from testbot.startup_status_presenter import print_startup_status" in source
    assert "from testbot.runtime_cli_args import parse_args" in source
    assert "from testbot.source_ingestion_startup import run_source_ingestion" in source
    assert "from testbot.source_ingestion_entry import apply_source_ingestion_entry" in source
    assert "def _apply_source_ingestion_selection" not in source
    assert "from testbot.sat_chatbot_memory_v2 import" not in source


def test_runtime_loop_owner_uses_canonical_turn_pipeline_helper_not_monolith_turn_pipeline_helper() -> None:
    from testbot.entrypoints import runtime_loop

    source = Path(runtime_loop.__file__).read_text()
    assert "from testbot.entrypoints.runtime_background_ingestion import (" in source
    assert "from testbot.entrypoints.runtime_commit_persistence import (" in source
    assert "from testbot.entrypoints.runtime_turn_pipeline import RuntimeTurnPipelineHooks, run_runtime_turn_pipeline" in source
    assert "from testbot.entrypoints.runtime_turn_telemetry import RuntimeTurnTelemetryDependencies, emit_runtime_turn_telemetry" in source
    assert "from testbot.application.services import answer_stage_runtime as answer_stage_runtime_service" in source
    assert "_poll_pending_ingestion_obligations(" not in source
    assert "_process_background_ingestion_completion(" not in source
    assert "_run_canonical_turn_pipeline(" not in source
    assert "_intent_telemetry_payload(" not in source
    assert "_build_debug_turn_payload(" not in source
    assert "_format_debug_turn_trace_payload(" not in source
    assert "_resolve_answer_routing_for_stage" not in source
    assert "_answer_assemble_for_turn_service" not in source
    assert "_answer_validate_for_turn_service" not in source
    assert "_detect_capability_offer" not in source
    assert "run_canonical_turn_pipeline(" not in source
    assert "_legacy_runtime.answer_commit_persistence(" not in source
    assert "TurnPipelineDependencies(" not in source


def test_sat_cli_is_transitional_wrapper_to_canonical_cli() -> None:
    source = Path(sat_cli.__file__).read_text()
    assert "compatibility-only" in source
    assert "from .cli import main as cli_main" in source


def test_run_satellite_mode_uses_gateway_with_stable_stop_id(monkeypatch) -> None:
    spoken: list[str] = []

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())
    monkeypatch.setattr(runtime, "sat_say", lambda _client, _entity_id, text: spoken.append(text))

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "satellite"
            assert question == "Ask one memory-grounded question."
            assert timeout_s == 60.0
            assert recent_successful_channel_context is None
            assert interaction_policy.interaction_requirements == InteractionRequirements()
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)


    def _fake_run_chat_loop(*, read_user_utterance, send_assistant_text, **_kwargs):
        assert read_user_utterance() == "stop"
        send_assistant_text("ack")

    monkeypatch.setattr(runtime, "_run_chat_loop", _fake_run_chat_loop)
    monkeypatch.setattr(runtime, "AskGateway", SimpleNamespace(from_runtime=lambda _runtime: _FakeGateway()))

    runtime._run_satellite_mode(
        runtime={
            "ha_base_url": "http://localhost:8123",
            "ha_api_token": "token",
            "ha_satellite_entity_id": "assist_satellite.kitchen",
        },
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
    )

    assert spoken == [
        "v0 memory loop online. Say 'stop' to exit.",
        "ack",
    ]



def test_run_satellite_mode_uses_planner_selected_requirements(monkeypatch) -> None:
    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())
    monkeypatch.setattr(runtime, "sat_say", lambda *_args, **_kwargs: None)

    planned_requirements = InteractionRequirements(
        stable_id_required=True,
        deterministic_field_collection_required=True,
        open_text_preferred=False,
        sentence_style_fit="structured_sentence",
        machine_actionable=False,
    )

    monkeypatch.setattr(
        sat_runtime_modes,
        "select_interaction_policy_request",
        lambda **_kwargs: SimpleNamespace(
            request=InteractionPolicyRequest(
                intent="collect_turn_input",
                channel_context="satellite",
                task_flow_context="memory_chat_loop",
                interaction_requirements=planned_requirements,
                policy_id="test.policy.v1",
            ),
            interaction_requirements=planned_requirements,
        ),
    )

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "satellite"
            assert question == "Ask one memory-grounded question."
            assert timeout_s == 60.0
            assert recent_successful_channel_context is None
            assert interaction_policy.interaction_requirements == planned_requirements
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        assert read_user_utterance() == "stop"

    sat_runtime_modes.run_satellite_mode(
        runtime={"ha_base_url": "http://localhost:8123", "ha_api_token": "token", "ha_satellite_entity_id": "assist_satellite.kitchen"},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )


def test_run_cli_mode_uses_terminal_channel_ask_gateway(monkeypatch) -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "cli"
            assert question == "Ask one memory-grounded question."
            assert timeout_s == 60.0
            assert recent_successful_channel_context is None
            assert interaction_policy.interaction_requirements == InteractionRequirements(
                stable_id_required=False,
                deterministic_field_collection_required=False,
                open_text_preferred=True,
                sentence_style_fit="plain_sentence",
                machine_actionable=False,
            )
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        assert capability_status == "ask_available"
        assert read_user_utterance() == "stop"

    sat_runtime_modes.run_cli_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )


def test_run_cli_mode_passes_non_stop_sentence_through_unchanged() -> None:
    sentence = "What did I ask you about source ingestion earlier?"

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert interaction_policy.channel_context == "cli"
            assert question == "Ask one memory-grounded question."
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence=sentence, error=None)

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == sentence


@pytest.mark.parametrize(
    ("decision_id", "sentence"),
    [
        (STOP_DECISION_ID, ""),
        ("cancelled", ""),
        ("user_aborted", ""),
        ("eof", ""),
        (None, "stop"),
        (None, "cancel"),
        (None, "EXIT"),
    ],
)
def test_run_cli_mode_collapses_terminal_stop_signals_to_stop(decision_id: str | None, sentence: str) -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=decision_id, sentence=sentence, error=None)

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == "stop"


def test_run_cli_mode_reports_retryable_ask_errors_as_retry_prompt() -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence="", error="temporary timeout from ask")

    observed: dict[str, object] = {}
    output = StringIO()

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    with redirect_stdout(output):
        sat_runtime_modes.run_cli_mode(
            runtime={},
            llm=SimpleNamespace(),
            store=SimpleNamespace(),
            chat_history=deque(),
            near_tie_delta=0.05,
            capability_snapshot=SimpleNamespace(),
            clock=SimpleNamespace(),
            ask_gateway=_FakeGateway(),
            run_chat_loop=_fake_run_chat_loop,
        )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == ""
    assert "Please try again." in output.getvalue()


def test_run_cli_mode_stops_on_non_retryable_ask_errors() -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence="", error="permission denied")

    observed: dict[str, object] = {}
    output = StringIO()

    def _fake_run_chat_loop(*, read_user_utterance, capability_status, **_kwargs):
        observed["capability_status"] = capability_status
        observed["utterance"] = read_user_utterance()

    with redirect_stdout(output):
        sat_runtime_modes.run_cli_mode(
            runtime={},
            llm=SimpleNamespace(),
            store=SimpleNamespace(),
            chat_history=deque(),
            near_tie_delta=0.05,
            capability_snapshot=SimpleNamespace(),
            clock=SimpleNamespace(),
            ask_gateway=_FakeGateway(),
            run_chat_loop=_fake_run_chat_loop,
        )

    assert observed["capability_status"] == "ask_available"
    assert observed["utterance"] == "stop"
    assert "Ask input is unavailable (permission denied). Stopping." in output.getvalue()


def test_run_cli_mode_handles_empty_ask_reply_as_silence() -> None:
    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(decision_id=None, sentence="   ", error=None)

    output = StringIO()
    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    with redirect_stdout(output):
        sat_runtime_modes.run_cli_mode(
            runtime={},
            llm=SimpleNamespace(),
            store=SimpleNamespace(),
            chat_history=deque(),
            near_tie_delta=0.05,
            capability_snapshot=SimpleNamespace(),
            clock=SimpleNamespace(),
            ask_gateway=_FakeGateway(),
            run_chat_loop=_fake_run_chat_loop,
        )

    assert observed["utterance"] == ""
    assert "bot> I heard silence. Try again." in output.getvalue()


def test_run_cli_mode_persists_last_successful_ask_channel_as_cli() -> None:
    runtime_state: dict[str, object] = {}

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(
                decision_id=None,
                sentence="What did I ask about earlier?",
                error=None,
                resolved_channel="terminal",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["utterance"] == "What did I ask about earlier?"
    assert runtime_state["last_successful_ask_channel_context"] == "cli"


def test_run_satellite_mode_persists_last_successful_ask_channel_as_satellite(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())
    monkeypatch.setattr(runtime, "sat_say", lambda *_args, **_kwargs: None)

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(
                decision_id=None,
                sentence="Tell me what changed.",
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert observed["utterance"] == "Tell me what changed."
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


@pytest.mark.parametrize(
    "artifact_sentence",
    [
        "thank you for watching",
        "  THANK   YOU   FOR   WATCHING  ",
        "thanks for listening",
        "see you next time",
        "subtitles by",
        "thank you thank you thank you thank you",
    ],
)
def test_run_satellite_mode_rejects_low_information_transcript_artifacts(
    monkeypatch: pytest.MonkeyPatch, artifact_sentence: str
) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }

    spoken: list[str] = []

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context is None
            return AskTurnInput(
                decision_id=None,
                sentence=artifact_sentence,
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda _client, _entity_id, text: spoken.append(text),
    )

    assert observed["utterance"] == ""
    assert spoken == [
        "v0 memory loop online. Say 'stop' to exit.",
        "I heard a low-information transcript artifact. Please try again.",
    ]
    assert "last_successful_ask_channel_context" not in runtime_state


def test_run_satellite_mode_artifact_rejection_does_not_overwrite_recent_successful_channel_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "last_successful_ask_channel_context": "satellite",
    }
    captured_recent: dict[str, object] = {}

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            captured_recent["value"] = recent_successful_channel_context
            return AskTurnInput(
                decision_id=None,
                sentence="thank you for listening",
                error=None,
                resolved_channel="satellite",
                resolution_source="recent_successful_ask_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert captured_recent["value"] == "satellite"
    assert observed["utterance"] == ""
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


def test_run_satellite_mode_keeps_meaningful_sentence_when_non_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }
    sentence = "What changed in runtime acceptance policy?"

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            return AskTurnInput(
                decision_id=None,
                sentence=sentence,
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda *_args, **_kwargs: None,
    )

    assert observed["utterance"] == sentence
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


def test_artifact_context_matrix_is_explicit_and_deterministic() -> None:
    question = "Ask one memory-grounded question."

    high_artifact_low_context = sat_runtime_modes._classify_artifact_vs_context(
        sentence="thank you for watching",
        question=question,
    )
    assert high_artifact_low_context.likely_artifact is True
    assert high_artifact_low_context.context_consistent is False
    assert high_artifact_low_context.should_reject is True
    assert "exact_known_phrase" in high_artifact_low_context.artifact_reasons

    high_artifact_higher_context = sat_runtime_modes._classify_artifact_vs_context(
        sentence="thanks for watching, can you answer my memory question about source ingestion?",
        question=question,
    )
    assert high_artifact_higher_context.likely_artifact is True
    assert high_artifact_higher_context.context_consistent is True
    assert high_artifact_higher_context.should_reject is False

    repeated_loop = sat_runtime_modes._classify_artifact_vs_context(
        sentence="thank you thank you thank you thank you",
        question=question,
    )
    assert repeated_loop.likely_artifact is True
    assert repeated_loop.context_consistent is False
    assert repeated_loop.should_reject is True
    assert "repeated_low_information_loop" in repeated_loop.artifact_reasons

    normal_meaningful_sentence = sat_runtime_modes._classify_artifact_vs_context(
        sentence="What changed in runtime acceptance policy?",
        question=question,
    )
    assert normal_meaningful_sentence.likely_artifact is False
    assert normal_meaningful_sentence.context_consistent is True
    assert normal_meaningful_sentence.should_reject is False
    assert normal_meaningful_sentence.artifact_reasons == ()


def test_run_satellite_mode_allows_context_consistent_sentence_with_artifact_substring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_state: dict[str, object] = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }
    sentence = "Thanks for watching, my memory question is about source ingestion."
    spoken: list[str] = []

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(sat_runtime_modes, "Client", lambda *_args, **_kwargs: _FakeClient())

    class _FakeGateway:
        ha_api_token = "token"
        satellite_entity_id = "assist_satellite.kitchen"

        def normalized_ha_rest_url(self) -> str:
            return "http://localhost:8123/api"

        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            return AskTurnInput(
                decision_id=None,
                sentence=sentence,
                error=None,
                resolved_channel="satellite",
                resolution_source="explicit_policy_channel",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_satellite_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda _client, _entity_id, text: spoken.append(text),
    )

    assert observed["utterance"] == sentence
    assert spoken == ["v0 memory loop online. Say 'stop' to exit."]
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"


def test_run_cli_mode_uses_recent_successful_channel_when_policy_channel_unavailable() -> None:
    runtime_state: dict[str, object] = {"last_successful_ask_channel_context": "cli"}
    captured_recent: dict[str, object] = {}

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            captured_recent["value"] = recent_successful_channel_context
            return AskTurnInput(
                decision_id=None,
                sentence="continue",
                error=None,
                resolved_channel="terminal",
                resolution_source="recent_successful_ask_channel",
                fallback_used=True,
                fallback_reason="policy_and_override_unavailable",
            )

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert captured_recent["value"] == "cli"
    assert observed["utterance"] == "continue"
    assert runtime_state["last_successful_ask_channel_context"] == "cli"


@pytest.mark.parametrize(
    ("ask_result", "expected_utterance"),
    [
        (AskTurnInput(decision_id=None, sentence="", error="temporary timeout from ask", resolved_channel="terminal"), ""),
        (AskTurnInput(decision_id=None, sentence="", error="permission denied", resolved_channel="terminal"), "stop"),
        (AskTurnInput(decision_id=None, sentence="   ", error=None, resolved_channel="terminal"), ""),
        (AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None, resolved_channel="terminal"), "stop"),
    ],
)
def test_run_cli_mode_error_empty_and_stop_paths_do_not_overwrite_recent_successful_channel(
    ask_result: AskTurnInput, expected_utterance: str
) -> None:
    runtime_state: dict[str, object] = {"last_successful_ask_channel_context": "satellite"}

    class _FakeGateway:
        def request_turn_input_for_policy(
            self,
            *,
            interaction_policy: InteractionPolicyRequest,
            question: str,
            timeout_s: float = 60.0,
            recent_successful_channel_context: str | None = None,
        ) -> AskTurnInput:
            assert recent_successful_channel_context == "satellite"
            return ask_result

    observed: dict[str, object] = {}

    def _fake_run_chat_loop(*, read_user_utterance, **_kwargs):
        observed["utterance"] = read_user_utterance()

    sat_runtime_modes.run_cli_mode(
        runtime=runtime_state,
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
    )

    assert observed["utterance"] == expected_utterance
    assert runtime_state["last_successful_ask_channel_context"] == "satellite"

def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False
    assert args.source_ingestion == "env"
    assert args.source_reference == "wikipedia_hilbert"
    assert args.source_freeform == ""


def test_parse_args_satellite_daemon() -> None:
    args = parse_args(["--mode", "satellite", "--daemon"])
    assert args.mode == "satellite"
    assert args.daemon is True
    assert args.source_ingestion == "env"


def test_parse_args_source_ingestion_selection() -> None:
    args = parse_args(["--source-ingestion", "reference", "--source-reference", "local_alignment_docs"])
    assert args.source_ingestion == "reference"
    assert args.source_reference == "local_alignment_docs"




def test_parse_args_debug_verbose_defaults_to_none() -> None:
    args = parse_args([])
    assert args.debug_verbose is None


def test_parse_args_debug_verbose_opt_in() -> None:
    args = parse_args(["--debug-verbose"])
    assert args.debug_verbose is True


def test_parse_args_debug_verbose_opt_out() -> None:
    args = parse_args(["--no-debug-verbose"])
    assert args.debug_verbose is False


def test_ha_connection_error_normalizes_url_before_connect(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class _FakeClient:
        def __init__(self, api_url: str, token: str) -> None:
            captured["api_url"] = api_url
            captured["token"] = token

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(runtime, "Client", _FakeClient)

    error = runtime._ha_connection_error("http://localhost:8123", "secret", "assist_satellite.kitchen")

    assert error is None
    assert captured["api_url"] == "http://localhost:8123/api/"
    assert captured["token"] == "secret"


def test_ha_connection_error_preserves_exception_class_and_message(monkeypatch) -> None:
    class _BoomClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def __enter__(self):
            raise RuntimeError("boom")

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(runtime, "Client", _BoomClient)

    error = runtime._ha_connection_error("http://localhost:8123", "secret", "assist_satellite.kitchen")

    assert error == "RuntimeError: boom"


def _load_live_smoke_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "smoke" / "run_live_smoke.py"
    spec = importlib.util.spec_from_file_location("testbot_live_smoke_module", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_env_loads_ollama_values_from_process_env(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:21143")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:latest")
    monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1")
    monkeypatch.setenv("X_OLLAMA_KEY", "x-ollama-test-key")

    runtime_env = runtime._read_runtime_env()

    assert runtime_env["ollama_base_url"] == "http://127.0.0.1:21143"
    assert runtime_env["ollama_model"] == "llama3.2:latest"
    assert runtime_env["ollama_embedding_model"] == "nomic-embed-text:v1"
    assert runtime_env["x_ollama_key"] == "x-ollama-test-key"


def test_runtime_and_live_smoke_resolve_ollama_env_from_same_process_env(monkeypatch) -> None:
    monkeypatch.setenv("HA_API_URL", "http://127.0.0.1:8123")
    monkeypatch.setenv("HA_API_TOKEN", "ha-test-supersecret-token")
    monkeypatch.setenv("HA_SATELLITE_ENTITY_ID", "assist_satellite.test")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:latest")
    monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    monkeypatch.setenv("X_OLLAMA_KEY", "shared-ollama-key")
    monkeypatch.setenv("SMOKE_CONNECT_TIMEOUT_S", "2")
    monkeypatch.setenv("SMOKE_REQUEST_TIMEOUT_S", "3")

    smoke_module = _load_live_smoke_module()
    smoke_env = smoke_module._load_required_env()
    runtime_env = runtime._read_runtime_env()

    assert runtime_env["ollama_base_url"] == smoke_env["OLLAMA_BASE_URL"]
    assert runtime_env["ollama_model"] == smoke_env["OLLAMA_MODEL"]
    assert runtime_env["ollama_embedding_model"] == smoke_env["OLLAMA_EMBEDDING_MODEL"]
    assert runtime_env["x_ollama_key"] == "shared-ollama-key"

def test_read_runtime_env_debug_verbose_defaults_false(monkeypatch) -> None:
    monkeypatch.delenv("TESTBOT_DEBUG_VERBOSE", raising=False)
    runtime_env = runtime._read_runtime_env()
    assert runtime_env["debug_verbose"] is False


def test_read_runtime_env_debug_verbose_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("TESTBOT_DEBUG_VERBOSE", "1")
    runtime_env = runtime._read_runtime_env()
    assert runtime_env["debug_verbose"] is True


def test_build_capability_snapshot_passes_x_ollama_key_to_connectivity_probe(monkeypatch) -> None:
    captured = {"x_ollama_key": None}

    monkeypatch.setattr(runtime, "_ha_connection_error", lambda *_args, **_kwargs: None)

    def _fake_ollama_probe(_base_url, _chat_model, _embedding_model, *, x_ollama_key=None):
        captured["x_ollama_key"] = x_ollama_key
        return None

    monkeypatch.setattr(runtime, "_ollama_connection_error", _fake_ollama_probe)

    runtime.build_capability_snapshot(
        requested_mode="auto",
        daemon_mode=False,
        runtime={
            "ha_base_url": "http://localhost:8123",
            "ha_api_token": "token",
            "ha_satellite_entity_id": "assist_satellite.kitchen",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3.1:latest",
            "ollama_embedding_model": "nomic-embed-text",
            "x_ollama_key": "probe-key",
            "memory_store_backend": "in_memory",
            "debug_verbose": False,
        },
    )

    assert captured["x_ollama_key"] == "probe-key"

def test_resolve_mode_prefers_satellite_when_ha_available() -> None:
    assert resolve_mode("auto", None) == "satellite"


def test_resolve_mode_falls_back_to_cli_when_ha_unavailable() -> None:
    assert resolve_mode("auto", "auth failed") == "cli"
    assert resolve_mode("cli", "auth failed") == "cli"




def test_validate_ollama_base_url_rejects_missing_scheme() -> None:
    err = runtime._validate_ollama_base_url("localhost:11434")
    assert err == "Invalid OLLAMA_BASE_URL 'localhost:11434'; must be full http(s) URL"


def test_validate_ollama_base_url_rejects_empty_string() -> None:
    err = runtime._validate_ollama_base_url("")
    assert err == "Invalid OLLAMA_BASE_URL ''; must be full http(s) URL"


def test_validate_ollama_base_url_rejects_unsupported_scheme() -> None:
    err = runtime._validate_ollama_base_url("ftp://localhost:11434")
    assert err == "Invalid OLLAMA_BASE_URL 'ftp://localhost:11434'; must be full http(s) URL"


def test_ollama_connection_error_returns_validation_error_before_urlopen(monkeypatch) -> None:
    called = {"urlopen": False}

    def _unexpected_urlopen(*_args, **_kwargs):
        called["urlopen"] = True
        raise AssertionError("urlopen should not be called for invalid base URL")

    monkeypatch.setattr(runtime_capability_service, "urlopen", _unexpected_urlopen)

    err = runtime_capability_service.ollama_connection_error("localhost:11434", "llama3.1:latest", "nomic-embed-text")

    assert err == "Invalid OLLAMA_BASE_URL 'localhost:11434'; must be full http(s) URL"
    assert called["urlopen"] is False
def test_ollama_connection_error_accepts_implicit_latest_alias(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"},{"model":"nomic-embed-text:latest"}]}'

    monkeypatch.setattr(runtime_capability_service, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime_capability_service.ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text")
    assert err is None


def test_ollama_connection_error_includes_x_ollama_key_when_configured(monkeypatch) -> None:
    observed = {"x_ollama_key": None}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"},{"model":"nomic-embed-text:latest"}]}'

    def _fake_urlopen(request, **_kwargs):
        observed["x_ollama_key"] = request.get_header("X-ollama-key")
        return _Resp()

    monkeypatch.setattr(runtime_capability_service, "urlopen", _fake_urlopen)
    err = runtime_capability_service.ollama_connection_error(
        "http://localhost:11434",
        "llama3.1:latest",
        "nomic-embed-text",
        x_ollama_key="test-key",
    )
    assert err is None
    assert observed["x_ollama_key"] == "test-key"


def test_ollama_connection_error_accepts_explicit_latest_alias(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"},{"model":"nomic-embed-text"}]}'

    monkeypatch.setattr(runtime_capability_service, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime_capability_service.ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text:latest")
    assert err is None


def test_ollama_connection_error_detects_missing_embedding_model(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"}]}'

    monkeypatch.setattr(runtime_capability_service, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime_capability_service.ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text")
    assert "embedding model" in str(err)


def _patch_main_dependencies(
    monkeypatch,
    *,
    args,
    ha_error: str | None,
    ollama_error: str | None,
    calls: dict[str, int],
    startup: dict | None = None,
    runtime_overrides: dict | None = None,
) -> None:
    runtime_env = {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text:latest",
        "memory_near_tie_delta": 0.02,
        "memory_store_mode": "inmemory",
        "elasticsearch_url": "http://localhost:9200",
        "elasticsearch_index": "testbot_memory_cards",
        "source_ingest_background_future": None,
        "source_ingest_background_in_progress": False,
    }

    if runtime_overrides:
        runtime_env.update(runtime_overrides)

    monkeypatch.setattr(cli, "parse_args", lambda _argv=None: args)
    monkeypatch.setattr(cli, "read_runtime_env", lambda: runtime_env)
    monkeypatch.setattr(runtime, "_ha_connection_error", lambda *_args, **_kwargs: ha_error)
    monkeypatch.setattr(runtime, "_ollama_connection_error", lambda *_args, **_kwargs: ollama_error)

    def _fake_build_capability_snapshot(*, requested_mode: str, daemon_mode: bool, runtime: dict[str, object]):
        if ollama_error is not None:
            effective_mode = None
            fallback_reason = None
            exit_reason = f"Ollama is unavailable: {ollama_error}"
        elif requested_mode == "auto" and ha_error is not None and daemon_mode:
            effective_mode = None
            fallback_reason = None
            exit_reason = f"Home Assistant is unavailable: {ha_error}"
        else:
            selected_mode = resolve_mode(requested_mode, ha_error)
            if selected_mode == "satellite" and ha_error is not None:
                if daemon_mode:
                    effective_mode = None
                    fallback_reason = None
                    exit_reason = f"Home Assistant is unavailable: {ha_error}"
                else:
                    effective_mode = "cli"
                    fallback_reason = "satellite connection is unavailable"
                    exit_reason = None
            else:
                effective_mode = selected_mode
                fallback_reason = None
                exit_reason = None

        return SimpleNamespace(
            requested_mode=requested_mode,
            daemon_mode=daemon_mode,
            effective_mode=effective_mode,
            fallback_reason=fallback_reason,
            exit_reason=exit_reason,
            ha_error=ha_error,
            ollama_error=ollama_error,
            runtime_capability_status=SimpleNamespace(
                debug_enabled=False,
                debug_verbose=bool(runtime.get("debug_verbose", False)),
                text_clarification_available=True,
                satellite_ask_available=(effective_mode == "satellite"),
            ),
        )

    monkeypatch.setattr(cli, "build_capability_snapshot", _fake_build_capability_snapshot)
    if startup is not None:
        def _capture_startup(**kwargs):
            startup.update(kwargs)
            snapshot = kwargs.get("snapshot")
            if snapshot is not None:
                startup.update(
                    {
                        "requested_mode": snapshot.requested_mode,
                        "effective_mode": snapshot.effective_mode,
                        "fallback_reason": snapshot.fallback_reason,
                    }
                )

        monkeypatch.setattr(cli, "print_startup_status", _capture_startup)
    else:
        monkeypatch.setattr(cli, "print_startup_status", lambda **_kwargs: None)
    monkeypatch.setattr(cli, "ChatOllama", lambda *a, **k: object())
    monkeypatch.setattr(cli, "OllamaEmbeddings", lambda *a, **k: object())
    monkeypatch.setattr(cli, "build_runtime_memory_store", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli, "append_session_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "run_source_ingestion",
        lambda **_kwargs: calls.__setitem__("ingestion", calls["ingestion"] + 1) if "ingestion" in calls else None,
    )
    monkeypatch.setattr(cli, "run_cli_mode", lambda **_kwargs: calls.__setitem__("cli", calls["cli"] + 1))
    monkeypatch.setattr(cli, "run_satellite_mode", lambda **_kwargs: calls.__setitem__("satellite", calls["satellite"] + 1))


def test_main_auto_daemon_ha_unavailable_exits_without_cli_fallback(monkeypatch, capsys) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=True)
    _patch_main_dependencies(
        monkeypatch,
        args=args,
        ha_error="auth failed",
        ollama_error=None,
        calls=calls,
        runtime_overrides={"memory_store_backend": "in_memory"},
    )

    runtime.main([])

    captured = capsys.readouterr()
    assert "Daemon mode requested in auto mode and Home Assistant is unavailable" in captured.err
    assert calls == {"cli": 0, "satellite": 0}


def test_main_auto_daemon_ha_available_uses_satellite(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=True)
    _patch_main_dependencies(monkeypatch, args=args, ha_error=None, ollama_error=None, calls=calls)

    runtime.main([])

    assert calls == {"cli": 0, "satellite": 1}


def test_main_passes_argv_to_entrypoint_parse_args(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    captured: dict[str, object] = {}

    def _parse(argv):
        captured["argv"] = argv
        return SimpleNamespace(mode="cli", daemon=False, debug_verbose=None)

    _patch_main_dependencies(
        monkeypatch,
        args=SimpleNamespace(mode="cli", daemon=False, debug_verbose=None),
        ha_error=None,
        ollama_error=None,
        calls=calls,
    )
    monkeypatch.setattr(cli, "parse_args", _parse)

    runtime.main(["--mode", "cli"])

    assert captured["argv"] == ["--mode", "cli"]


def test_main_kicks_off_source_ingestion_and_applies_debug_verbose_override(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0, "ingestion": 0}
    startup: dict[str, object] = {}
    runtime_env: dict[str, object] = {"debug_verbose": False}

    _patch_main_dependencies(
        monkeypatch,
        args=SimpleNamespace(mode="cli", daemon=False, debug_verbose=True),
        ha_error=None,
        ollama_error=None,
        calls=calls,
        startup=startup,
        runtime_overrides=runtime_env,
    )

    def _capture_cli(**kwargs):
        captured_runtime = kwargs["runtime"]
        assert captured_runtime["debug_verbose"] is True
        calls["cli"] += 1

    monkeypatch.setattr(cli, "run_cli_mode", _capture_cli)

    runtime.main([])

    assert startup["effective_mode"] == "cli"
    assert calls["ingestion"] == 1


def test_main_cli_source_ingestion_selection_is_authoritative_over_env(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    runtime_env: dict[str, object] = {
        "source_ingest_enabled": False,
        "source_connector_type": "fixture",
    }
    observed: dict[str, object] = {}

    _patch_main_dependencies(
        monkeypatch,
        args=SimpleNamespace(mode="cli", daemon=False, debug_verbose=None, source_ingestion="wikipedia"),
        ha_error=None,
        ollama_error=None,
        calls=calls,
        runtime_overrides=runtime_env,
    )

    def _capture_ingestion(*, runtime: dict[str, object], **_kwargs):
        observed["enabled"] = runtime["source_ingest_enabled"]
        observed["connector"] = runtime["source_connector_type"]
        observed["selected_via"] = runtime["source_ingest_selection_source"]

    monkeypatch.setattr(cli, "run_source_ingestion", _capture_ingestion)
    runtime.main([])

    assert observed == {
        "enabled": True,
        "connector": "wikipedia",
        "selected_via": "cli",
    }


def test_main_uses_domain_clock_provider_for_cli_wiring(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    provided_clock = object()
    captured: dict[str, object] = {}

    _patch_main_dependencies(
        monkeypatch,
        args=SimpleNamespace(mode="cli", daemon=False, debug_verbose=None),
        ha_error=None,
        ollama_error=None,
        calls=calls,
    )
    monkeypatch.setattr(cli, "build_system_clock", lambda: provided_clock)

    def _capture_cli(**kwargs):
        captured["clock"] = kwargs["clock"]
        calls["cli"] += 1

    monkeypatch.setattr(cli, "run_cli_mode", _capture_cli)
    runtime.main([])

    assert calls["cli"] == 1
    assert captured["clock"] is provided_clock


def test_main_satellite_mode_reports_cli_as_effective_mode_when_fallback_applies(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    startup: dict[str, object] = {}
    args = SimpleNamespace(mode="satellite", daemon=False)
    _patch_main_dependencies(monkeypatch, args=args, ha_error="auth failed", ollama_error=None, calls=calls, startup=startup)

    runtime.main([])

    assert calls == {"cli": 1, "satellite": 0}
    assert startup["requested_mode"] == "satellite"
    assert startup["effective_mode"] == "cli"
    assert startup["fallback_reason"] == "satellite connection is unavailable"




def test_main_auto_non_daemon_ha_unavailable_emits_cli_fallback_and_continuity_messages(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=False)
    captured: dict[str, str] = {}

    original_print_startup_status = runtime.print_startup_status

    def _capture_startup_output(**kwargs):
        stream = StringIO()
        with redirect_stdout(stream):
            original_print_startup_status(**kwargs)
        captured["output"] = stream.getvalue()

    _patch_main_dependencies(
        monkeypatch,
        args=args,
        ha_error="auth failed",
        ollama_error=None,
        calls=calls,
        runtime_overrides={"memory_store_backend": "in_memory"},
    )
    monkeypatch.setattr(cli, "print_startup_status", _capture_startup_output)

    runtime.main([])

    assert calls == {"cli": 1, "satellite": 0}
    output = captured["output"]
    assert "CLI fallback will be used unless --daemon is set" in output
    assert "Continuity: memory cards are shared across interfaces in-process via one vector store." in output

def test_main_auto_non_daemon_ollama_unavailable_exits_early(monkeypatch, capsys) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=False)
    _patch_main_dependencies(monkeypatch, args=args, ha_error=None, ollama_error="missing models", calls=calls)

    runtime.main([])

    captured = capsys.readouterr()
    assert "Startup failed and Ollama is unavailable" in captured.err
    assert calls == {"cli": 0, "satellite": 0}


def test_main_daemon_ollama_unavailable_exits_early(monkeypatch, capsys) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="satellite", daemon=True)
    _patch_main_dependencies(monkeypatch, args=args, ha_error=None, ollama_error="missing models", calls=calls)

    runtime.main([])

    captured = capsys.readouterr()
    assert "Startup failed and Ollama is unavailable" in captured.err
    assert calls == {"cli": 0, "satellite": 0}


def test_run_source_ingestion_stores_fixture_docs_and_logs(monkeypatch, tmp_path) -> None:
    fixture_path = tmp_path / "ingest_fixture.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "item_id": "src-1",
                    "content": "Task: utility bill due Friday",
                    "source_uri": "ha://tasks/utility-bill",
                    "retrieved_at": "2026-03-10T09:00:00Z",
                    "trust_tier": "verified",
                    "metadata": {"ts": "2026-03-14T00:00:00Z"},
                }
            ]
        ),
        encoding="utf-8",
    )

    class _Store:
        def __init__(self) -> None:
            self.docs = []

        def add_memory_records(self, records):
            self.docs.extend(records)

    logs = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    runtime._run_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 10,
            "source_ingest_cursor": None,
        },
        store=_Store(),
    )

    assert logs
    assert logs[-1][0] == "source_ingest_completed"
    assert logs[-1][1]["stored_count"] == 2


def test_run_source_ingestion_skips_unsupported_connector(monkeypatch) -> None:
    logs = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    runtime._run_source_ingestion(
        runtime={"source_ingest_enabled": True, "source_connector_type": "unknown", "source_fixture_path": ""},
        store=object(),
    )

    assert logs[-1][0] == "source_ingest_skipped"
    assert logs[-1][1]["reason"] == "unsupported_connector_type"




def test_build_source_connector_supports_local_markdown(monkeypatch, tmp_path) -> None:
    logs = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    connector = runtime._build_source_connector(
        {
            "source_ingest_enabled": True,
            "source_connector_type": "local_markdown",
            "source_markdown_path": str(tmp_path),
        }
    )

    assert connector is not None
    assert connector.source_type == "local_markdown"
    assert logs == []


def test_build_source_connector_supports_wikipedia(monkeypatch) -> None:
    logs = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    connector = runtime._build_source_connector(
        {
            "source_ingest_enabled": True,
            "source_connector_type": "wikipedia",
            "source_wikipedia_topic": "OpenAI",
            "source_wikipedia_language": "en",
        }
    )

    assert connector is not None
    assert connector.source_type == "wikipedia"
    assert logs == []


def test_build_source_connector_supports_arxiv(monkeypatch) -> None:
    logs = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    connector = runtime._build_source_connector(
        {
            "source_ingest_enabled": True,
            "source_connector_type": "arxiv",
            "source_arxiv_query": "cat:cs.AI",
        }
    )

    assert connector is not None
    assert connector.source_type == "arxiv"
    assert logs == []

def test_read_runtime_env_invalid_numerics_fallback(monkeypatch, caplog) -> None:
    monkeypatch.setenv("MEMORY_NEAR_TIE_DELTA", "not-a-float")
    monkeypatch.setenv("SOURCE_INGEST_LIMIT", "not-an-int")

    with caplog.at_level("WARNING"):
        runtime_env = runtime._read_runtime_env()

    assert runtime_env["memory_near_tie_delta"] == 0.02
    assert runtime_env["source_ingest_limit"] == 50
    assert "Invalid MEMORY_NEAR_TIE_DELTA" in caplog.text
    assert "Invalid SOURCE_INGEST_LIMIT" in caplog.text


def test_run_source_ingestion_invalid_cursor_logs_and_falls_back(monkeypatch, tmp_path) -> None:
    fixture_path = tmp_path / "ingest_fixture.json"
    fixture_path.write_text(
        json.dumps([
            {
                "item_id": "src-1",
                "content": "Task: utility bill due Friday",
                "source_uri": "ha://tasks/utility-bill",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": "verified",
                "metadata": {"ts": "2026-03-14T00:00:00Z"},
            }
        ]),
        encoding="utf-8",
    )

    class _Store:
        def add_memory_records(self, records):
            del records

    logs = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    runtime._run_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 10,
            "source_ingest_cursor": "bad-cursor",
        },
        store=_Store(),
    )

    assert logs[0][0] == "source_ingest_cursor_invalid"
    assert logs[0][1]["cursor"] == "bad-cursor"
    assert logs[-1][0] == "source_ingest_completed"


def test_run_source_ingestion_failure_logs_and_does_not_raise(monkeypatch, capsys, tmp_path) -> None:
    fixture_path = tmp_path / "ingest_fixture.json"
    fixture_path.write_text(
        json.dumps([
            {
                "item_id": "src-1",
                "content": "Task: utility bill due Friday",
                "source_uri": "ha://tasks/utility-bill",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": "verified",
                "metadata": {"ts": "2026-03-14T00:00:00Z"},
            }
        ]),
        encoding="utf-8",
    )

    class _FailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise RuntimeError("boom")

    logs = []
    monkeypatch.setattr("testbot.source_ingestion_startup.SourceIngestor", _FailingIngestor)
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))

    runtime._run_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 5,
            "source_ingest_cursor": "12",
        },
        store=object(),
    )

    captured = capsys.readouterr()
    assert "continuing without ingested source documents" in captured.err
    assert logs[-1][0] == "source_ingest_failed"
    assert logs[-1][1]["source_type"] == "fixture"
    assert logs[-1][1]["cursor"] == "12"
    assert logs[-1][1]["limit"] == 5
    assert logs[-1][1]["exception_class"] == "RuntimeError"
    assert logs[-1][1]["exception_message"] == "boom"


def test_main_reaches_cli_when_source_ingestion_fails(monkeypatch, tmp_path) -> None:
    class _FailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise RuntimeError("ingest failed")

    fixture_path = tmp_path / "ingest_fixture.json"
    fixture_path.write_text(
        json.dumps([
            {
                "item_id": "src-1",
                "content": "Task: utility bill due Friday",
                "source_uri": "ha://tasks/utility-bill",
                "retrieved_at": "2026-03-10T09:00:00Z",
                "trust_tier": "verified",
                "metadata": {"ts": "2026-03-14T00:00:00Z"},
            }
        ]),
        encoding="utf-8",
    )

    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="cli", daemon=False)
    _patch_main_dependencies(
        monkeypatch,
        args=args,
        ha_error=None,
        ollama_error=None,
        calls=calls,
        runtime_overrides={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 5,
            "source_ingest_cursor": None,
        },
    )
    monkeypatch.setattr(runtime, "SourceIngestor", _FailingIngestor)

    runtime.main([])

    assert calls == {"cli": 1, "satellite": 0}


def test_main_reaches_cli_when_source_connector_fetch_raises_http_error(monkeypatch) -> None:
    class _FetchFailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise HTTPError(
                url="https://example.invalid/source",
                code=503,
                msg="upstream unavailable",
                hdrs=None,
                fp=None,
            )

    calls = {"cli": 0, "satellite": 0}
    logs: list[tuple[str, dict[str, object]]] = []
    args = SimpleNamespace(mode="cli", daemon=False)
    _patch_main_dependencies(
        monkeypatch,
        args=args,
        ha_error=None,
        ollama_error=None,
        calls=calls,
        runtime_overrides={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": "unused.json",
            "source_ingest_limit": 5,
            "source_ingest_cursor": None,
        },
    )
    monkeypatch.setattr("testbot.source_ingestion_startup.SourceIngestor", _FetchFailingIngestor)
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(cli, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr("testbot.source_ingestion_startup.build_source_connector", lambda **_kwargs: SimpleNamespace(source_type="fixture"))
    monkeypatch.setattr(cli, "run_source_ingestion", runtime.run_source_ingestion)

    runtime.main([])

    assert calls == {"cli": 1, "satellite": 0}
    assert logs[-1][0] == "source_ingest_failed"
    assert logs[-1][1]["exception_class"] == "HTTPError"


def test_main_reaches_cli_when_source_store_add_documents_raises(monkeypatch) -> None:
    class _StoreFailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise RuntimeError("embedding backend unavailable")

    calls = {"cli": 0, "satellite": 0}
    logs: list[tuple[str, dict[str, object]]] = []
    args = SimpleNamespace(mode="cli", daemon=False)
    _patch_main_dependencies(
        monkeypatch,
        args=args,
        ha_error=None,
        ollama_error=None,
        calls=calls,
        runtime_overrides={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": "unused.json",
            "source_ingest_limit": 5,
            "source_ingest_cursor": None,
        },
    )
    monkeypatch.setattr("testbot.source_ingestion_startup.SourceIngestor", _StoreFailingIngestor)
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(cli, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr("testbot.source_ingestion_startup.build_source_connector", lambda **_kwargs: SimpleNamespace(source_type="fixture"))
    monkeypatch.setattr(cli, "run_source_ingestion", runtime.run_source_ingestion)

    runtime.main([])

    assert calls == {"cli": 1, "satellite": 0}
    assert logs[-1][0] == "source_ingest_failed"
    assert logs[-1][1]["exception_class"] == "RuntimeError"
    assert logs[-1][1]["exception_message"] == "embedding backend unavailable"


def test_resolve_turn_intent_affirmation_preserves_clarification_intent() -> None:
    prior_state = runtime.PipelineState(
        user_input="what happened?",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer=CLARIFY_ANSWER,
    )

    classified, resolved = resolve_turn_intent(utterance="yes", prior_pipeline_state=prior_state)

    assert classified.value == "knowledge_question"
    assert resolved.value == "memory_recall"


def test_resolve_turn_intent_non_affirmation_does_not_preserve_prior_intent() -> None:
    prior_state = runtime.PipelineState(
        user_input="what happened?",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer=CLARIFY_ANSWER,
    )

    classified, resolved = resolve_turn_intent(utterance="no, never mind", prior_pipeline_state=prior_state)

    assert classified.value == "control"
    assert resolved.value == "control"


def test_resolve_turn_intent_temporal_followup_after_memory_recall_avoids_knowledge_question_fallback() -> None:
    prior_state = runtime.PipelineState(
        user_input="Who am I?",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer="You are Sam.",
        commit_receipt={"confirmed_user_facts": ["name=Sam"]},
    )

    classified, resolved = resolve_turn_intent(utterance="when was that again?", prior_pipeline_state=prior_state)

    assert classified.value == "knowledge_question"
    assert resolved.value == "time_query"


def test_execute_source_ingestion_returns_failed_payload(monkeypatch) -> None:
    class _FailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise RuntimeError("boom")

    monkeypatch.setattr(runtime, "SourceIngestor", _FailingIngestor)
    monkeypatch.setattr(runtime, "_build_source_connector", lambda _runtime: SimpleNamespace(source_type="fixture"))

    result = runtime._execute_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_ingest_limit": 5,
            "source_ingest_cursor": "12",
        },
        store=object(),
    )

    assert result["ok"] is False
    assert result["status"] == "failed"
    assert result["payload"]["exception_class"] == "RuntimeError"



def test_background_source_ingestion_start_generates_namespaced_request_id(monkeypatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []

    def _fake_execute(*, runtime: dict[str, object], store, background: bool = False, ingestion_request_id: str = ""):
        del runtime, store
        return {"ok": True, "status": "completed", "payload": {"background": background, "stored_count": 1, "ingestion_request_id": ingestion_request_id}}

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(runtime, "_execute_source_ingestion", _fake_execute)

    rt = {
        "source_ingest_background_future": None,
        "source_ingest_background_in_progress": False,
        "source_ingest_background_request_id": "",
        "active_ingestion_request_id": "turn-doc-legacy",
    }
    started = runtime._start_background_source_ingestion(runtime=rt, store=object())

    assert started["started"] is True
    assert str(started["ingestion_request_id"]).startswith("ingest-req-")
    assert started["ingestion_request_id"] != "turn-doc-legacy"
    assert logs[0][0] == "source_ingest_background_started"
    assert logs[0][1]["ingestion_request_id"] == started["ingestion_request_id"]


def test_chat_loop_registers_pending_ingestion_context_by_request_id(monkeypatch) -> None:
    from testbot.entrypoints import runtime_loop

    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **kwargs: None)

    def _pipeline(**kwargs):
        state = kwargs["state"]
        from dataclasses import replace

        return (
            replace(
                state,
                final_answer="Pending ingest answer.",
                candidate_facts={"turn_id": "turn-doc-123"},
                same_turn_exclusion={"excluded_doc_ids": ["turn-doc-123", "reflection-doc-123"]},
                commit_receipt={"pending_ingestion_request_id": "ingest-req-123"},
                invariant_decisions={"fallback_action": "NONE", "answer_mode": "knowing"},
                confidence_decision={"stage_audit_trail": []},
                provenance_types=[],
                claims=[],
                used_memory_refs=[],
                used_source_evidence_refs=[],
                source_evidence_attribution=[],
                basis_statement="source evidence",
            ),
            [],
        )

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _pipeline)

    rt: dict[str, object] = {"seed": True}
    prompts = iter(["What changed?", "stop"])
    runtime._run_chat_loop(
        runtime=rt,
        llm=object(),
        store=object(),
        chat_history=runtime.deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=runtime.CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=runtime.RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda _text: None,
        clock=type("_Clock", (), {"now": staticmethod(lambda: __import__('arrow').get("2026-03-10T11:00:00+00:00"))})(),
    )

    pending_registry = rt.get("pending_ingestion_registry")
    assert isinstance(pending_registry, dict)
    pending = pending_registry.get("ingest-req-123")
    assert pending is not None
    assert pending["ingestion_request_id"] == "ingest-req-123"
    assert pending["utterance"] == "What changed?"
    assert pending["source_context"]["utterance_doc_id"] == "turn-doc-123"
    assert pending["source_context"]["same_turn_exclusion_doc_ids"] == ["turn-doc-123", "reflection-doc-123"]
    assert pending["status"] == "pending"
    assert pending["attempt_count"] >= 0
    assert pending["created_at"]
    assert pending["last_polled_at"]
    assert pending["deadline_at"]

    created_events = [payload for name, payload in events if name == "source_ingest_obligation_transition" and payload.get("status") == "created"]
    assert created_events
    assert created_events[-1]["ingestion_request_id"] == "ingest-req-123"


def test_poll_pending_ingestion_obligations_times_out_and_dead_letters(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))

    rt: dict[str, object] = {
        "pending_ingestion_registry": {
            "ingest-1": {
                "ingestion_request_id": "ingest-1",
                "utterance": "What changed?",
                "created_at": "2026-03-10T10:00:00+00:00",
                "last_polled_at": "2026-03-10T10:00:00+00:00",
                "attempt_count": 2,
                "deadline_at": "2026-03-10T10:30:00+00:00",
                "status": "pending",
            }
        },
        "dead_letter_ingestion_registry": {},
    }

    monkeypatch.setattr(runtime.arrow, "utcnow", lambda: runtime.arrow.get("2026-03-10T11:00:00+00:00"))

    runtime._poll_pending_ingestion_obligations(runtime=rt)

    assert rt["pending_ingestion_registry"] == {}
    assert "ingest-1" in rt["dead_letter_ingestion_registry"]
    dead = rt["dead_letter_ingestion_registry"]["ingest-1"]
    assert dead["status"] == "timed_out"
    assert dead["attempt_count"] == 3
    assert events[-1][0] == "source_ingest_obligation_transition"
    assert events[-1][1]["ingestion_request_id"] == "ingest-1"
    assert events[-1][1]["status"] == "timed_out"


def test_chat_loop_polls_pending_ingestion_obligation_each_turn(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "_process_background_ingestion_completion", lambda **kwargs: ("", None, False))

    runtime._run_chat_loop(
        runtime={
            "pending_ingestion_registry": {
                "ingest-2": {
                    "ingestion_request_id": "ingest-2",
                    "utterance": "pending",
                    "created_at": "2026-03-10T10:00:00+00:00",
                    "last_polled_at": "2026-03-10T10:00:00+00:00",
                    "attempt_count": 0,
                    "deadline_at": "2099-03-10T12:00:00+00:00",
                    "status": "pending",
                }
            }
        },
        llm=object(),
        store=object(),
        chat_history=runtime.deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=runtime.CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=runtime.RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: "stop",
        send_assistant_text=lambda _text: None,
        clock=type("_Clock", (), {"now": staticmethod(lambda: __import__('arrow').get("2026-03-10T11:00:00+00:00"))})(),
    )

    polled_events = [
        payload for name, payload in events if name == "source_ingest_obligation_transition" and payload.get("status") == "polled_pending"
    ]
    assert polled_events
    assert polled_events[-1]["ingestion_request_id"] == "ingest-2"

def test_background_source_ingestion_start_and_poll_completion(monkeypatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []
    from testbot.entrypoints import runtime_background_ingestion

    def _fake_execute(*, runtime: dict[str, object], store, background: bool = False, ingestion_request_id: str = ""):
        del runtime, store
        return {"ok": True, "status": "completed", "payload": {"background": background, "stored_count": 2, "ingestion_request_id": ingestion_request_id}}

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(
        runtime_background_ingestion,
        "execute_source_ingestion",
        lambda *, runtime, store, deps, background=False, ingestion_request_id="": _fake_execute(
            runtime=runtime,
            store=store,
            background=background,
            ingestion_request_id=ingestion_request_id,
        ),
    )

    rt = {"source_ingest_background_future": None, "source_ingest_background_in_progress": False, "source_ingest_background_request_id": ""}
    started = runtime._start_background_source_ingestion(runtime=rt, store=object(), ingestion_request_id="turn-abc")

    assert started["started"] is True
    assert started["ingestion_request_id"] == "turn-abc"
    assert logs[0][0] == "source_ingest_background_started"
    assert logs[0][1]["ingestion_request_id"] == "turn-abc"

    while True:
        polled = runtime._poll_background_source_ingestion(runtime=rt)
        if polled and polled.get("status") != "running":
            break

    assert polled is not None
    assert polled["ok"] is True
    assert rt["source_ingest_background_in_progress"] is False
    assert logs[-1][0] == "source_ingest_completed"
    assert logs[-1][1]["background"] is True
    assert logs[-1][1]["ingestion_request_id"] == "turn-abc"


def test_cli_mode_proactively_emits_completion_without_extra_prompt(monkeypatch) -> None:
    from testbot.entrypoints import runtime_background_ingestion, runtime_loop

    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **kwargs: None)

    class _Clock:
        def now(self):
            import arrow

            return arrow.get("2026-03-10T11:00:00+00:00")

    poll_calls = {"count": 0}

    def _poll(*, runtime: dict[str, object]):
        poll_calls["count"] += 1
        if poll_calls["count"] == 1:
            return {
                "ok": True,
                "status": "completed",
                "payload": {"ingestion_request_id": "turn-123", "background": True, "stored_count": 2},
            }
        return None

    monkeypatch.setattr(
        runtime_background_ingestion,
        "poll_background_source_ingestion",
        lambda *, runtime, deps: _poll(runtime=runtime),
    )

    def _pipeline(**kwargs):
        state = kwargs["state"]
        from dataclasses import replace

        return (
            replace(
                state,
                final_answer="Grounded answer after ingestion.",
                commit_receipt={"pending_ingestion_request_id": ""},
                invariant_decisions={"fallback_action": "NONE", "answer_mode": "knowing"},
                confidence_decision={"stage_audit_trail": []},
                provenance_types=[],
                claims=[],
                used_memory_refs=[],
                used_source_evidence_refs=["src-900"],
                source_evidence_attribution=[],
                basis_statement="source evidence",
            ),
            [],
        )

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _pipeline)

    replies: list[str] = []
    prompts = iter(["stop"])
    runtime._run_chat_loop(
        runtime={
            "pending_ingestion_registry": {
                "turn-123": {"utterance": "What is due Friday?", "prior_pipeline_state": None}
            }
        },
        llm=object(),
        store=object(),
        chat_history=runtime.deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=runtime.CapabilitySnapshot(
            runtime={},
            requested_mode="cli",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason=None,
            exit_reason=None,
            ha_error=None,
            ollama_error=None,
            runtime_capability_status=runtime.RuntimeCapabilityStatus(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="cli",
                daemon_mode=False,
                fallback_reason=None,
                memory_backend="inmemory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        ),
        read_user_utterance=lambda: next(prompts, None),
        send_assistant_text=lambda text: replies.append(text),
        clock=_Clock(),
    )

    assert replies[0].startswith("Background ingestion completed for request turn-123")
    assert replies[1] == "Grounded answer after ingestion."
    assert replies[-1] == "Stopping. Bye."
