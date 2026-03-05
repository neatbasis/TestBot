from __future__ import annotations

import json
from types import SimpleNamespace

from testbot.sat_chatbot_memory_v2 import _parse_args, _resolve_mode
from testbot import sat_chatbot_memory_v2 as runtime


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False


def test_parse_args_satellite_daemon() -> None:
    args = _parse_args(["--mode", "satellite", "--daemon"])
    assert args.mode == "satellite"
    assert args.daemon is True


def test_resolve_mode_prefers_satellite_when_ha_available() -> None:
    assert _resolve_mode("auto", None) == "satellite"


def test_resolve_mode_falls_back_to_cli_when_ha_unavailable() -> None:
    assert _resolve_mode("auto", "auth failed") == "cli"
    assert _resolve_mode("cli", "auth failed") == "cli"


def test_ollama_connection_error_detects_missing_embedding_model(monkeypatch) -> None:
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models":[{"model":"llama3.1:latest"}]}'

    monkeypatch.setattr(runtime, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime._ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text")
    assert "embedding model" in str(err)


def _patch_main_dependencies(
    monkeypatch,
    *,
    args,
    ha_error: str | None,
    ollama_error: str | None,
    calls: dict[str, int],
    startup: dict | None = None,
) -> None:
    runtime_env = {
        "ha_api_url": "http://localhost:8123",
        "ha_api_secret": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text",
        "memory_near_tie_delta": 0.02,
        "memory_store_mode": "inmemory",
        "elasticsearch_url": "http://localhost:9200",
        "elasticsearch_index": "testbot_memory_cards",
    }

    monkeypatch.setattr(runtime, "_parse_args", lambda _argv=None: args)
    monkeypatch.setattr(runtime, "_read_runtime_env", lambda: runtime_env)
    monkeypatch.setattr(runtime, "_ha_connection_error", lambda *_args, **_kwargs: ha_error)
    monkeypatch.setattr(runtime, "_ollama_connection_error", lambda *_args, **_kwargs: ollama_error)
    if startup is not None:
        monkeypatch.setattr(runtime, "_print_startup_status", lambda **kwargs: startup.update(kwargs))
    else:
        monkeypatch.setattr(runtime, "_print_startup_status", lambda **_kwargs: None)
    monkeypatch.setattr(runtime, "ChatOllama", lambda *a, **k: object())
    monkeypatch.setattr(runtime, "OllamaEmbeddings", lambda *a, **k: object())
    monkeypatch.setattr(runtime, "build_memory_store", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(runtime, "append_session_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runtime, "_run_cli_mode", lambda **_kwargs: calls.__setitem__("cli", calls["cli"] + 1))
    monkeypatch.setattr(runtime, "_run_satellite_mode", lambda **_kwargs: calls.__setitem__("satellite", calls["satellite"] + 1))


def test_main_auto_daemon_ha_unavailable_exits_without_cli_fallback(monkeypatch, capsys) -> None:
    calls = {"cli": 0, "satellite": 0}
    args = SimpleNamespace(mode="auto", daemon=True)
    _patch_main_dependencies(monkeypatch, args=args, ha_error="auth failed", ollama_error=None, calls=calls)

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

        def add_documents(self, docs):
            self.docs.extend(docs)

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
        def add_documents(self, docs):
            del docs

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
