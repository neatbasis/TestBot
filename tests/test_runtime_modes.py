from __future__ import annotations

from types import SimpleNamespace

from testbot.sat_chatbot_memory_v2 import _parse_args, _resolve_mode
from testbot import sat_chatbot_memory_v2 as runtime


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False
    assert args.debug is False


def test_parse_args_satellite_daemon() -> None:
    args = _parse_args(["--mode", "satellite", "--daemon", "--debug"])
    assert args.mode == "satellite"
    assert args.daemon is True
    assert args.debug is True


def test_resolve_mode_prefers_satellite_when_ha_available() -> None:
    assert _resolve_mode("auto", None) == "satellite"


def test_resolve_mode_falls_back_to_cli_when_ha_unavailable() -> None:
    assert _resolve_mode("auto", "auth failed") == "cli"
    assert _resolve_mode("cli", "auth failed") == "cli"


def _patch_main_dependencies(monkeypatch, *, args, ha_error: str | None, calls: dict[str, int], startup: dict | None = None) -> None:
    runtime_env = {
        "ha_api_url": "http://localhost:8123",
        "ha_api_secret": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "memory_near_tie_delta": 0.02,
        "output_mode": "normal",
    }

    monkeypatch.setattr(runtime, "_parse_args", lambda _argv=None: args)
    monkeypatch.setattr(runtime, "_read_runtime_env", lambda: runtime_env)
    monkeypatch.setattr(runtime, "_ha_connection_error", lambda *_args, **_kwargs: ha_error)
    if startup is not None:
        monkeypatch.setattr(runtime, "_print_startup_status", lambda **kwargs: startup.update(kwargs))
    else:
        monkeypatch.setattr(runtime, "_print_startup_status", lambda **_kwargs: None)
    monkeypatch.setattr(runtime, "ChatOllama", lambda *a, **k: object())
    monkeypatch.setattr(runtime, "OllamaEmbeddings", lambda *a, **k: object())
    monkeypatch.setattr(runtime, "InMemoryVectorStore", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(runtime, "append_session_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runtime, "_run_cli_mode", lambda **_kwargs: calls.__setitem__("cli", calls["cli"] + 1))
    monkeypatch.setattr(runtime, "_run_satellite_mode", lambda **_kwargs: calls.__setitem__("satellite", calls["satellite"] + 1))


def test_main_auto_daemon_ha_unavailable_exits_without_cli_fallback(monkeypatch, capsys) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=True, debug=False)
    _patch_main_dependencies(monkeypatch, args=args, ha_error="auth failed", calls=calls)

    runtime.main([])

    captured = capsys.readouterr()
    assert "Daemon mode requested in auto mode and Home Assistant is unavailable" in captured.err
    assert calls == {"cli": 0, "satellite": 0}


def test_main_auto_daemon_ha_available_uses_satellite(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=True, debug=False)
    _patch_main_dependencies(monkeypatch, args=args, ha_error=None, calls=calls)

    runtime.main([])

    assert calls == {"cli": 0, "satellite": 1}


def test_main_satellite_mode_reports_cli_as_effective_mode_when_fallback_applies(monkeypatch) -> None:
    calls = {"cli": 0, "satellite": 0}
    startup: dict[str, object] = {}
    args = SimpleNamespace(mode="satellite", daemon=False, debug=False)
    _patch_main_dependencies(monkeypatch, args=args, ha_error="auth failed", calls=calls, startup=startup)

    runtime.main([])

    assert calls == {"cli": 1, "satellite": 0}
    assert startup["requested_mode"] == "satellite"
    assert startup["effective_mode"] == "cli"
    assert startup["fallback_reason"] == "satellite connection is unavailable"
