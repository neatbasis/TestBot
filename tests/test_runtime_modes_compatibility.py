from __future__ import annotations

import importlib.util
import json
from contextlib import redirect_stdout
from io import StringIO
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from testbot.entrypoints import cli
from testbot.adapters.ask_gateway import AskTurnInput, STOP_DECISION_ID
from testbot.entrypoints import sat_cli
from testbot.entrypoints import sat_runtime_modes
from testbot.entrypoints import runtime_background_ingestion
from testbot.entrypoints import runtime_bootstrap
from testbot.entrypoints import runtime_loop
from testbot.entrypoints import runtime_turn_pipeline
from testbot.entrypoints.runtime_legacy_bridge import read_runtime_env
from testbot.interaction_policy import InteractionPolicyRequest
from testbot.interaction_standards import InteractionRequirements
from testbot.runtime_capability_service import resolve_mode
from testbot.runtime_cli_args import parse_args
from testbot.application.services import context_retrieval_runtime
from testbot.answer_contract_constants import CLARIFY_ANSWER
from testbot.application.services.intent_routing_diagnostics import resolve_turn_intent
from testbot.source_ingestion_startup import (
    build_source_connector as build_startup_source_connector,
    run_source_ingestion as run_startup_source_ingestion,
)
from testbot import sat_chatbot_memory_v2 as runtime
import testbot.runtime_capability_service as runtime_capability_service


def test_entrypoints_package_exposes_lazy_main_wrapper_without_eager_sat_cli_import() -> None:
    source = Path("src/testbot/entrypoints/__init__.py").read_text()
    assert "from .sat_cli import main\n" not in source
    assert "def main(" in source
    assert "from .cli import main as cli_main" in source


def test_runtime_legacy_bridge_warns_on_monolith_compat_usage() -> None:
    with pytest.deprecated_call(match="runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2"):
        read_runtime_env()


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


def test_legacy_capabilities_help_answer_helper_delegates_to_canonical_continuity_owner() -> None:
    from testbot.application.services import continuity_runtime

    samples = [
        "Runtime mode: cli\nMemory recall: available\nHome Assistant: unavailable",
        "not a capabilities payload",
    ]

    for text in samples:
        assert runtime._is_capabilities_help_answer(text) is continuity_runtime.is_capabilities_help_answer(text)


def test_sat_cli_is_transitional_wrapper_to_canonical_cli() -> None:
    source = Path(sat_cli.__file__).read_text()
    assert "compatibility-only" in source
    assert "from .cli import main as cli_main" in source

# SAT compatibility tranche migrated from tests/test_runtime_modes.py

def test_run_satellite_mode_uses_gateway_with_stable_stop_id(monkeypatch) -> None:
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
            assert interaction_policy.channel_context == "satellite"
            assert question == "Ask one memory-grounded question."
            assert timeout_s == 60.0
            assert recent_successful_channel_context is None
            assert interaction_policy.interaction_requirements == InteractionRequirements()
            return AskTurnInput(decision_id=STOP_DECISION_ID, sentence="", error=None)


    def _fake_run_chat_loop(*, read_user_utterance, send_assistant_text, **_kwargs):
        assert read_user_utterance() == "stop"
        send_assistant_text("ack")

    sat_runtime_modes.run_satellite_mode(
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
        ask_gateway=_FakeGateway(),
        run_chat_loop=_fake_run_chat_loop,
        satellite_say=lambda _client, _entity_id, text: spoken.append(text),
    )

    assert spoken == [
        "v0 memory loop online. Say 'stop' to exit.",
        "ack",
    ]


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

    runtime_env = runtime_bootstrap.read_runtime_env()

    assert runtime_env["ollama_base_url"] == "http://127.0.0.1:21143"
    assert runtime_env["ollama_model"] == "llama3.2:latest"
    assert runtime_env["ollama_embedding_model"] == "nomic-embed-text:v1"
    assert runtime_env["x_ollama_key"] == "x-ollama-test-key"


def test_runtime_and_live_smoke_resolve_ollama_env_from_same_process_env(monkeypatch) -> None:
    monkeypatch.setenv("HA_BASE_URL", "http://127.0.0.1:8123")
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
    runtime_env = runtime_bootstrap.read_runtime_env()

    assert runtime_env["ollama_base_url"] == smoke_env["OLLAMA_BASE_URL"]
    assert runtime_env["ollama_model"] == smoke_env["OLLAMA_MODEL"]
    assert runtime_env["ollama_embedding_model"] == smoke_env["OLLAMA_EMBEDDING_MODEL"]
    assert runtime_env["x_ollama_key"] == "shared-ollama-key"


def test_read_runtime_env_debug_verbose_defaults_false(monkeypatch) -> None:
    monkeypatch.delenv("TESTBOT_DEBUG_VERBOSE", raising=False)
    runtime_env = runtime_bootstrap.read_runtime_env()
    assert runtime_env["debug_verbose"] is False


def test_read_runtime_env_debug_verbose_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("TESTBOT_DEBUG_VERBOSE", "1")
    runtime_env = runtime_bootstrap.read_runtime_env()
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


def test_validate_ollama_base_url_rejects_missing_scheme() -> None:
    err = runtime._validate_ollama_base_url("localhost:11434")
    assert err == "Invalid OLLAMA_BASE_URL 'localhost:11434'; must be full http(s) URL"


def test_validate_ollama_base_url_rejects_empty_string() -> None:
    err = runtime._validate_ollama_base_url("")
    assert err == "Invalid OLLAMA_BASE_URL ''; must be full http(s) URL"


def test_validate_ollama_base_url_rejects_unsupported_scheme() -> None:
    err = runtime._validate_ollama_base_url("ftp://localhost:11434")
    assert err == "Invalid OLLAMA_BASE_URL 'ftp://localhost:11434'; must be full http(s) URL"


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

    run_startup_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 10,
            "source_ingest_cursor": None,
        },
        store=_Store(),
        append_session_log=lambda event, payload: logs.append((event, payload)),
    )

    assert logs
    assert logs[-1][0] == "source_ingest_completed"
    assert logs[-1][1]["stored_count"] == 2


def test_run_source_ingestion_skips_unsupported_connector(monkeypatch) -> None:
    logs = []

    run_startup_source_ingestion(
        runtime={"source_ingest_enabled": True, "source_connector_type": "unknown", "source_fixture_path": ""},
        store=object(),
        append_session_log=lambda event, payload: logs.append((event, payload)),
    )

    assert logs[-1][0] == "source_ingest_skipped"
    assert logs[-1][1]["reason"] == "unsupported_connector_type"


def test_build_source_connector_supports_local_markdown(monkeypatch, tmp_path) -> None:
    logs = []

    connector = build_startup_source_connector(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "local_markdown",
            "source_markdown_path": str(tmp_path),
        },
        append_session_log=lambda event, payload: logs.append((event, payload)),
    )

    assert connector is not None
    assert connector.source_type == "local_markdown"
    assert logs == []


def test_build_source_connector_supports_wikipedia(monkeypatch) -> None:
    logs = []

    connector = build_startup_source_connector(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "wikipedia",
            "source_wikipedia_topic": "OpenAI",
            "source_wikipedia_language": "en",
        },
        append_session_log=lambda event, payload: logs.append((event, payload)),
    )

    assert connector is not None
    assert connector.source_type == "wikipedia"
    assert logs == []


def test_build_source_connector_supports_arxiv(monkeypatch) -> None:
    logs = []

    connector = build_startup_source_connector(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "arxiv",
            "source_arxiv_query": "cat:cs.AI",
        },
        append_session_log=lambda event, payload: logs.append((event, payload)),
    )

    assert connector is not None
    assert connector.source_type == "arxiv"
    assert logs == []


def test_read_runtime_env_invalid_numerics_fallback(monkeypatch, caplog) -> None:
    monkeypatch.setenv("MEMORY_NEAR_TIE_DELTA", "not-a-float")
    monkeypatch.setenv("SOURCE_INGEST_LIMIT", "not-an-int")

    with caplog.at_level("WARNING"):
        runtime_env = runtime_bootstrap.read_runtime_env()

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

    run_startup_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 10,
            "source_ingest_cursor": "bad-cursor",
        },
        store=_Store(),
        append_session_log=lambda event, payload: logs.append((event, payload)),
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

    run_startup_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_fixture_path": str(fixture_path),
            "source_ingest_limit": 5,
            "source_ingest_cursor": "12",
        },
        store=object(),
        append_session_log=lambda event, payload: logs.append((event, payload)),
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


def test_execute_source_ingestion_returns_failed_payload(monkeypatch) -> None:
    class _FailingIngestor:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def ingest_once(self, *, cursor, limit):
            del cursor, limit
            raise RuntimeError("boom")

    deps = runtime_background_ingestion.RuntimeBackgroundIngestionDependencies(
        append_session_log=lambda _event, _payload: None,
        build_source_connector=lambda _runtime: SimpleNamespace(source_type="fixture"),
        source_ingestor_cls=_FailingIngestor,
        answer_commit_persistence=lambda **_kwargs: None,
        replay_background_completion_turn=lambda _request: runtime_loop.PipelineState(user_input=""),
    )

    result = runtime_background_ingestion.execute_source_ingestion(
        runtime={
            "source_ingest_enabled": True,
            "source_connector_type": "fixture",
            "source_ingest_limit": 5,
            "source_ingest_cursor": "12",
        },
        store=object(),
        deps=deps,
    )

    assert result["ok"] is False
    assert result["status"] == "failed"
    assert result["payload"]["exception_class"] == "RuntimeError"


def test_background_source_ingestion_start_generates_namespaced_request_id(monkeypatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []

    def _fake_execute(*, runtime: dict[str, object], store, background: bool = False, ingestion_request_id: str = ""):
        del runtime, store
        return {"ok": True, "status": "completed", "payload": {"background": background, "stored_count": 1, "ingestion_request_id": ingestion_request_id}}

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

    deps = runtime_background_ingestion.RuntimeBackgroundIngestionDependencies(
        append_session_log=lambda event, payload: logs.append((event, payload)),
        build_source_connector=lambda _runtime: None,
        source_ingestor_cls=object,
        answer_commit_persistence=lambda **_kwargs: None,
        replay_background_completion_turn=lambda _request: runtime_loop.PipelineState(user_input=""),
    )

    rt = {
        "source_ingest_background_future": None,
        "source_ingest_background_in_progress": False,
        "source_ingest_background_request_id": "",
        "active_ingestion_request_id": "turn-doc-legacy",
    }
    started = runtime_background_ingestion.start_background_source_ingestion(
        runtime=rt,
        store=object(),
        deps=deps,
    )

    assert started["started"] is True
    assert str(started["ingestion_request_id"]).startswith("ingest-req-")
    assert started["ingestion_request_id"] != "turn-doc-legacy"
    assert logs[0][0] == "source_ingest_background_started"
    assert logs[0][1]["ingestion_request_id"] == started["ingestion_request_id"]


def test_chat_loop_registers_pending_ingestion_context_by_request_id(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(runtime_loop, "append_runtime_session_log", lambda event, payload: events.append((event, payload)))
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
    runtime_loop.run_chat_loop(
        runtime=rt,
        llm=object(),
        store=object(),
        chat_history=deque(),
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
    deps = runtime_background_ingestion.RuntimeBackgroundIngestionDependencies(
        append_session_log=lambda event, payload: events.append((event, payload)),
        build_source_connector=lambda _runtime: None,
        source_ingestor_cls=object,
        answer_commit_persistence=lambda **_kwargs: None,
        replay_background_completion_turn=lambda _request: runtime_loop.PipelineState(user_input=""),
    )

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

    monkeypatch.setattr(
        runtime_background_ingestion.arrow,
        "utcnow",
        lambda: runtime_background_ingestion.arrow.get("2026-03-10T11:00:00+00:00"),
    )

    runtime_background_ingestion.poll_pending_ingestion_obligations(runtime=rt, deps=deps)

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
    monkeypatch.setattr(runtime_loop, "append_runtime_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **kwargs: ("", None, False))

    runtime_loop.run_chat_loop(
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
        chat_history=deque(),
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

    def _fake_execute(*, runtime: dict[str, object], store, background: bool = False, ingestion_request_id: str = ""):
        del runtime, store
        return {"ok": True, "status": "completed", "payload": {"background": background, "stored_count": 2, "ingestion_request_id": ingestion_request_id}}

    deps = runtime_background_ingestion.RuntimeBackgroundIngestionDependencies(
        append_session_log=lambda event, payload: logs.append((event, payload)),
        build_source_connector=lambda _runtime: None,
        source_ingestor_cls=object,
        answer_commit_persistence=lambda **_kwargs: None,
        replay_background_completion_turn=lambda _request: runtime_loop.PipelineState(user_input=""),
    )
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
    started = runtime_background_ingestion.start_background_source_ingestion(
        runtime=rt,
        store=object(),
        deps=deps,
        ingestion_request_id="turn-abc",
    )

    assert started["started"] is True
    assert started["ingestion_request_id"] == "turn-abc"
    assert logs[0][0] == "source_ingest_background_started"
    assert logs[0][1]["ingestion_request_id"] == "turn-abc"

    while True:
        polled = runtime_background_ingestion.poll_background_source_ingestion(runtime=rt, deps=deps)
        if polled and polled.get("status") != "running":
            break

    assert polled is not None
    assert polled["ok"] is True
    assert rt["source_ingest_background_in_progress"] is False
    assert logs[-1][0] == "source_ingest_completed"
    assert logs[-1][1]["background"] is True
    assert logs[-1][1]["ingestion_request_id"] == "turn-abc"


def test_cli_mode_proactively_emits_completion_without_extra_prompt(monkeypatch) -> None:
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

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _pipeline)

    replies: list[str] = []
    prompts = iter(["stop"])
    runtime_loop.run_chat_loop(
        runtime={
            "pending_ingestion_registry": {
                "turn-123": {"utterance": "What is due Friday?", "prior_pipeline_state": None}
            }
        },
        llm=object(),
        store=object(),
        chat_history=deque(),
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

# SAT boundary compatibility tests migrated from tests/test_runtime_modes.py

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

    monkeypatch.setattr(runtime_turn_pipeline, "run_runtime_turn_pipeline", _unexpected_pipeline_call)

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


def test_canonical_retrieve_policy_path_is_independent_from_legacy_monolith_helper() -> None:
    assert not hasattr(runtime, "_should_force_memory_retrieval_for_identity_recall")

    assert context_retrieval_runtime.should_force_memory_retrieval_for_identity_recall(
        utterance="who am i?",
        prior_state=runtime.PipelineState(user_input="my name is sam"),
        continuity_evidence=("commit.confirmed_user_facts:user_name",),
        context_history_anchors=(),
    )


def test_canonical_rerank_threshold_policy_path_is_independent_from_legacy_monolith_helper(
) -> None:
    assert not hasattr(runtime, "_assemble_rerank_threshold_profile_policy")

    policy = context_retrieval_runtime.assemble_rerank_threshold_profile_policy()

    assert isinstance(policy.top_final_score_min, float)
    assert isinstance(policy.min_margin_to_second, float)


def test_canonical_stage_rerank_path_is_independent_from_legacy_monolith_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _legacy_sabotage(*_args, **_kwargs):
        raise AssertionError("legacy stage_rerank must not be required for canonical rerank path")

    monkeypatch.setattr(runtime, "stage_rerank", _legacy_sabotage)

    state = runtime.PipelineState(user_input="who am i?", confidence_decision={})
    candidates = [
        context_retrieval_runtime.RetrievalInputRecord(
            ref_id="doc-1",
            score=0.9,
            content="candidate",
            metadata={"doc_id": "doc-1", "ts": "2026-03-10T11:30:00+00:00"},
        )
    ]

    class _Clock:
        def now(self):
            return runtime.arrow.get("2026-03-10T12:00:00+00:00")

    next_state, hits = context_retrieval_runtime.stage_rerank_for_turn_service(
        state,
        candidates,
        utterance="who am i?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=_Clock(),
    )

    assert isinstance(next_state, runtime.PipelineState)
    assert isinstance(hits, list)


def test_runtime_loop_turn_policy_logic_hooks_use_canonical_logic_owner_not_monolith(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.logic import turn_policy as turn_policy_logic

    observed_hooks: dict[str, object] = {}
    observed_telemetry_ambiguity_helpers: list[object] = []

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)
    monkeypatch.setattr(
        runtime,
        "_optional_string",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy _optional_string should not be used by canonical runtime-loop hook assembly")
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_ambiguity_score",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy _ambiguity_score should not be used by canonical runtime-loop hook/telemetry wiring")
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_selected_decision_from_confidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "legacy _selected_decision_from_confidence should not be used by canonical runtime-loop hook assembly"
            )
        ),
    )

    def _capture_hooks_and_finish(**kwargs):
        observed_hooks["hooks"] = kwargs["hooks"]
        return runtime_loop.PipelineState(
            user_input=kwargs["state"].user_input,
            last_user_message_ts=kwargs["state"].last_user_message_ts,
            classified_intent=kwargs["state"].classified_intent,
            resolved_intent="knowledge_question",
            prior_unresolved_intent=kwargs["state"].prior_unresolved_intent,
            confidence_decision={},
            final_answer="done",
            commit_receipt={},
        ), []

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _capture_hooks_and_finish)
    monkeypatch.setattr(runtime_loop.continuity_runtime_service, "apply_unresolved_intent_carryover", lambda state: state)
    monkeypatch.setattr(
        runtime_loop,
        "emit_runtime_turn_telemetry",
        lambda **kwargs: observed_telemetry_ambiguity_helpers.append(kwargs["deps"].ambiguity_score),
    )

    utterances = iter(["hello", None])
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
        read_user_utterance=lambda: next(utterances),
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-01-01T00:00:00+00:00")),
    )

    hooks = observed_hooks["hooks"]
    assert hooks.optional_string is turn_policy_logic.optional_string
    assert hooks.ambiguity_score is turn_policy_logic.ambiguity_score
    assert hooks.selected_decision_from_confidence is turn_policy_logic.selected_decision_from_confidence
    assert observed_telemetry_ambiguity_helpers == [turn_policy_logic.ambiguity_score]


def test_runtime_loop_turn_policy_policy_hooks_use_canonical_policy_owner_not_monolith(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.policies import turn_policy as turn_policy_policies

    observed_hooks: dict[str, object] = {}

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "emit_runtime_turn_telemetry", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)
    monkeypatch.setattr(
        runtime,
        "_intent_classifier_confidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy _intent_classifier_confidence should not be used by canonical runtime-loop hook assembly")
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_minimal_confidence_decision_for_direct_answer",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "legacy _minimal_confidence_decision_for_direct_answer should not be used by canonical runtime-loop hook assembly"
            )
        ),
    )

    def _capture_hooks_and_finish(**kwargs):
        observed_hooks["hooks"] = kwargs["hooks"]
        return runtime_loop.PipelineState(
            user_input=kwargs["state"].user_input,
            last_user_message_ts=kwargs["state"].last_user_message_ts,
            classified_intent=kwargs["state"].classified_intent,
            resolved_intent="knowledge_question",
            prior_unresolved_intent=kwargs["state"].prior_unresolved_intent,
            confidence_decision={},
            final_answer="done",
            commit_receipt={},
        ), []

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _capture_hooks_and_finish)
    monkeypatch.setattr(runtime_loop.continuity_runtime_service, "apply_unresolved_intent_carryover", lambda state: state)

    utterances = iter(["hello", None])
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
        read_user_utterance=lambda: next(utterances),
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-01-01T00:00:00+00:00")),
    )

    hooks = observed_hooks["hooks"]
    assert hooks.intent_classifier_confidence.func is turn_policy_policies.intent_classifier_confidence
    assert hooks.intent_classifier_confidence.keywords == {
        "confidence_threshold": turn_policy_policies.INTENT_CLASSIFIER_CONFIDENCE_THRESHOLD
    }
    assert hooks.minimal_confidence_decision_for_direct_answer.func is turn_policy_policies.minimal_confidence_decision_for_direct_answer
    assert hooks.minimal_confidence_decision_for_direct_answer.keywords == {
        "retrieval_score_threshold": turn_policy_policies.RETRIEVAL_SCORE_THRESHOLD
    }


def test_runtime_loop_turn_telemetry_deps_use_canonical_append_session_log(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.observability import session_log as session_log_module

    observed_telemetry_loggers: list[object] = []

    def _legacy_logger_guard(event: str, payload: dict[str, object]) -> None:
        del event, payload
        raise AssertionError("legacy append_session_log should not own runtime-loop telemetry or ingest logging")

    monkeypatch.setattr(runtime, "append_session_log", _legacy_logger_guard)
    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(
        runtime_loop,
        "run_runtime_turn_pipeline",
        lambda **kwargs: (
            runtime_loop.PipelineState(
                user_input=kwargs["state"].user_input,
                last_user_message_ts=kwargs["state"].last_user_message_ts,
                classified_intent=kwargs["state"].classified_intent,
                resolved_intent="knowledge_question",
                prior_unresolved_intent=kwargs["state"].prior_unresolved_intent,
                confidence_decision={},
                final_answer="ok",
                commit_receipt={},
            ),
            [],
        ),
    )
    monkeypatch.setattr(runtime_loop.continuity_runtime_service, "apply_unresolved_intent_carryover", lambda state: state)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)
    monkeypatch.setattr(
        runtime_loop,
        "emit_runtime_turn_telemetry",
        lambda **kwargs: observed_telemetry_loggers.append(kwargs["deps"].append_session_log),
    )

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
        read_user_utterance=iter(["Need telemetry proof", "stop"]).__next__,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-01-01T00:00:00+00:00")),
    )

    assert observed_telemetry_loggers == [session_log_module.append_session_log]
    observed_telemetry_loggers[0]("runtime_loop_turn_telemetry_logger_proof", {})


def test_runtime_loop_ingest_snapshot_time_provider_is_canonical_not_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    observed_time_provider_types: list[str] = []
    pipeline_called = {"value": False}

    def _capture_snapshot(stage, state, *, time_provider):
        observed_time_provider_types.append(type(time_provider).__name__)

    def _run_pipeline(**kwargs):
        pipeline_called["value"] = True
        state = kwargs["state"]
        return (
            runtime_loop.PipelineState(
                user_input=state.user_input,
                last_user_message_ts=state.last_user_message_ts,
                classified_intent=state.classified_intent,
                resolved_intent=state.resolved_intent,
                prior_unresolved_intent=state.prior_unresolved_intent,
                confidence_decision={},
                final_answer="ok",
                commit_receipt={},
            ),
            [],
        )

    monkeypatch.setattr(
        runtime,
        "_ClockBackedSnapshotTimeProvider",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy snapshot provider should not be used")),
    )
    monkeypatch.setattr(runtime_loop, "append_pipeline_snapshot", _capture_snapshot)
    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "emit_runtime_turn_telemetry", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop.continuity_runtime_service, "apply_unresolved_intent_carryover", lambda state: state)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _run_pipeline)

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
        read_user_utterance=iter(["Need update", "stop"]).__next__,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-03-10T11:00:00+00:00")),
    )

    assert pipeline_called["value"] is True
    assert observed_time_provider_types == ["RuntimeClockBackedSnapshotTimeProvider"]


def test_runtime_loop_pending_ingestion_created_transition_uses_canonical_runtime_background_ingestion_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from testbot.entrypoints import runtime_loop

    registrations: list[dict[str, object]] = []
    events: list[tuple[str, dict[str, object]]] = []

    def _register_pending(**kwargs):
        registrations.append(kwargs)
        return True

    assert not hasattr(runtime, "_emit_obligation_transition")
    monkeypatch.setattr(runtime_loop, "register_pending_ingestion_obligation", _register_pending)
    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "emit_runtime_turn_telemetry", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop.continuity_runtime_service, "apply_unresolved_intent_carryover", lambda state: state)
    monkeypatch.setattr(runtime_loop, "append_runtime_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)

    def _pipeline(**kwargs):
        state = kwargs["state"]
        return (
            runtime_loop.PipelineState(
                user_input=state.user_input,
                last_user_message_ts=state.last_user_message_ts,
                classified_intent=state.classified_intent,
                resolved_intent=state.resolved_intent,
                prior_unresolved_intent=state.prior_unresolved_intent,
                confidence_decision={},
                final_answer="pending",
                candidate_facts={"turn_id": "turn-doc-123"},
                same_turn_exclusion={"excluded_doc_ids": ["turn-doc-123"]},
                commit_receipt={"pending_ingestion_request_id": "ingest-req-123"},
            ),
            [],
        )

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _pipeline)

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
        read_user_utterance=iter(["What changed?", "stop"]).__next__,
        send_assistant_text=lambda _text: None,
        clock=SimpleNamespace(now=lambda: runtime.arrow.get("2026-03-10T11:00:00+00:00")),
    )

    assert registrations
    assert registrations[-1]["pending_request_id"] == "ingest-req-123"
    assert events


def test_runtime_loop_background_ingestion_connector_ingestor_dependencies_are_bound_to_canonical_owners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from testbot.entrypoints import runtime_loop

    captured: dict[str, object] = {}
    expected_connector = object()
    expected_runtime: dict[str, object] = {}

    class _CapturingDeps:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    class _LegacyIngestorShouldNotBeUsed:
        def __init__(self, **_kwargs) -> None:
            raise AssertionError("legacy background-ingestion ingestor class should not be used")

    monkeypatch.setattr(runtime, "SourceIngestor", _LegacyIngestorShouldNotBeUsed)
    monkeypatch.setattr(runtime_loop, "RuntimeBackgroundIngestionDependencies", _CapturingDeps)
    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(
        runtime_loop,
        "build_source_connector",
        lambda *, runtime, append_session_log: expected_connector if runtime is expected_runtime else None,
    )

    runtime_loop.run_chat_loop(
        runtime=expected_runtime,
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

    connector = captured["build_source_connector"]
    assert callable(connector)
    assert connector(expected_runtime) is expected_connector
    assert captured["source_ingestor_cls"] is runtime_loop.SourceIngestor


def test_runtime_loop_turn_pipeline_hook_logging_bundle_uses_canonical_session_logger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from testbot.entrypoints import runtime_loop
    from testbot.application.services.background_ingestion_runtime import BackgroundIngestionReplayRequest
    from testbot.observability.session_log import append_session_log as append_runtime_session_log

    captured: dict[str, object] = {}

    class _CapturingDeps:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    def _legacy_append_session_log_guard(event: str, payload: dict[str, object]) -> None:
        del event, payload
        raise AssertionError("selected turn-pipeline hook logging bundle should not use legacy append_session_log")

    monkeypatch.setattr(runtime, "append_session_log", _legacy_append_session_log_guard)
    monkeypatch.setattr(runtime_loop, "RuntimeBackgroundIngestionDependencies", _CapturingDeps)
    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(
        runtime_loop,
        "run_runtime_turn_pipeline",
        lambda **kwargs: (captured.setdefault("hooks", kwargs["hooks"]) and kwargs["state"], []),
    )

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

    replay = captured["replay_background_completion_turn"]
    replay(
        BackgroundIngestionReplayRequest(
            runtime={},
            llm=object(),
            store=object(),
            utterance="Need grounded update",
            last_user_message_ts="2026-01-01T00:00:00+00:00",
            prior_pipeline_state=None,
            near_tie_delta=0.1,
            chat_history=deque(),
            capability_status="ok",
            capability_snapshot={},
            clock=object(),
            io_channel="cli",
            turn_id="turn-1",
        )
    )

    hooks = captured["hooks"]
    assert hooks.append_session_log is append_runtime_session_log

    observed: dict[str, object] = {}
    monkeypatch.setattr(
        runtime_loop.answer_stage_runtime_service,
        "answer_assemble_for_turn_service",
        lambda *_args, **kwargs: observed.update(kwargs) or object(),
    )
    hooks.answer_assemble(
        object(),
        runtime_loop.PipelineState(
            user_input="probe",
            last_user_message_ts="",
            classified_intent="knowledge_question",
            resolved_intent="",
            prior_unresolved_intent="",
            confidence_decision={},
        ),
        chat_history=deque(),
        hits=[],
        capability_status="ok",
        answer_routing=object(),
    )
    assert observed["append_session_log"] is append_runtime_session_log


def test_runtime_loop_stage_retrieve_canonical_path_does_not_depend_on_legacy_stage_retrieve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    from testbot.application.services import context_retrieval_runtime as context_retrieval_runtime_service
    from testbot.entrypoints import runtime_loop

    captured: dict[str, object] = {}

    monkeypatch.setattr(runtime_loop, "poll_pending_ingestion_obligations", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "process_background_ingestion_completion", lambda **_kwargs: ("", None, False))
    monkeypatch.setattr(runtime_loop, "emit_runtime_turn_telemetry", lambda **_kwargs: None)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)

    def _fake_turn_pipeline(**kwargs):
        captured["hooks"] = kwargs["hooks"]
        state = kwargs["state"]
        return (
            replace(
                state,
                final_answer="ok",
                commit_receipt={"pending_ingestion_request_id": ""},
            ),
            [],
        )

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _fake_turn_pipeline)
    monkeypatch.setattr(
        runtime,
        "stage_retrieve",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("legacy stage_retrieve should not be used by canonical runtime-loop retrieval hook")
        ),
    )

    observed: dict[str, object] = {}

    def _fake_stage_retrieve_for_turn_service(*args, **kwargs):
        observed["kwargs"] = kwargs
        return args[1], []

    monkeypatch.setattr(
        context_retrieval_runtime_service,
        "stage_retrieve_for_turn_service",
        _fake_stage_retrieve_for_turn_service,
    )

    utterances = iter(["hello", "stop"])
    runtime_loop.run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.1,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=object(),
        read_user_utterance=lambda: next(utterances, None),
        send_assistant_text=lambda _text: None,
        clock=runtime.SystemClock(),
    )

    hooks = captured["hooks"]
    probe_state = runtime.PipelineState(user_input="probe", rewritten_query="probe")
    hooks.stage_retrieve(object(), probe_state)

    assert observed["kwargs"]["retrieval_score_threshold"] == runtime.RETRIEVAL_SCORE_THRESHOLD
    assert "stage_retrieve_fn" not in observed["kwargs"]
