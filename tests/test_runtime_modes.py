from __future__ import annotations

import importlib.util
import json
from collections import deque
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError

from testbot.sat_chatbot_memory_v2 import CLARIFY_ANSWER, parse_args, resolve_mode, resolve_turn_intent
from testbot import sat_chatbot_memory_v2 as runtime




def test_run_satellite_mode_uses_single_ask_prompt(monkeypatch) -> None:
    spoken: list[str] = []

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(runtime, "normalize_rest_api_url", lambda url: url)
    monkeypatch.setattr(runtime, "Client", lambda *_args, **_kwargs: _FakeClient())
    monkeypatch.setattr(runtime, "sat_say", lambda _client, _entity_id, text: spoken.append(text))
    monkeypatch.setattr(runtime, "ask_question", lambda **_kwargs: {"sentence": "stop"})

    def _fake_run_chat_loop(*, read_user_utterance, send_assistant_text, **_kwargs):
        utterance = read_user_utterance()
        assert utterance == "stop"
        send_assistant_text("ack")

    monkeypatch.setattr(runtime, "_run_chat_loop", _fake_run_chat_loop)

    runtime._run_satellite_mode(
        runtime={},
        llm=SimpleNamespace(),
        store=SimpleNamespace(),
        chat_history=deque(),
        near_tie_delta=0.05,
        api_url="http://localhost:8123",
        token="token",
        entity_id="assist_satellite.kitchen",
        capability_snapshot=SimpleNamespace(),
        clock=SimpleNamespace(),
    )

    assert spoken == [
        "v0 memory loop online. Say 'stop' to exit.",
        "ack",
    ]

def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False


def test_parse_args_satellite_daemon() -> None:
    args = parse_args(["--mode", "satellite", "--daemon"])
    assert args.mode == "satellite"
    assert args.daemon is True




def test_parse_args_debug_verbose_defaults_to_none() -> None:
    args = parse_args([])
    assert args.debug_verbose is None


def test_parse_args_debug_verbose_opt_in() -> None:
    args = parse_args(["--debug-verbose"])
    assert args.debug_verbose is True


def test_parse_args_debug_verbose_opt_out() -> None:
    args = parse_args(["--no-debug-verbose"])
    assert args.debug_verbose is False




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
    monkeypatch.setenv("HA_API_SECRET", "ha-test-supersecret-token")
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
            "ha_api_url": "http://localhost:8123",
            "ha_api_secret": "token",
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

    monkeypatch.setattr(runtime, "urlopen", _unexpected_urlopen)

    err = runtime._ollama_connection_error("localhost:11434", "llama3.1:latest", "nomic-embed-text")

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

    monkeypatch.setattr(runtime, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime._ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text")
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

    monkeypatch.setattr(runtime, "urlopen", _fake_urlopen)
    err = runtime._ollama_connection_error(
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

    monkeypatch.setattr(runtime, "urlopen", lambda *_args, **_kwargs: _Resp())
    err = runtime._ollama_connection_error("http://localhost:11434", "llama3.1:latest", "nomic-embed-text:latest")
    assert err is None


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
    runtime_overrides: dict | None = None,
) -> None:
    runtime_env = {
        "ha_api_url": "http://localhost:8123",
        "ha_api_secret": "token",
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

    monkeypatch.setattr(runtime, "_parse_args", lambda _argv=None: args)
    monkeypatch.setattr(runtime, "_read_runtime_env", lambda: runtime_env)
    monkeypatch.setattr(runtime, "_ha_connection_error", lambda *_args, **_kwargs: ha_error)
    monkeypatch.setattr(runtime, "_ollama_connection_error", lambda *_args, **_kwargs: ollama_error)
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

        monkeypatch.setattr(runtime, "_print_startup_status", _capture_startup)
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

    original_print_startup_status = runtime._print_startup_status

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
    monkeypatch.setattr(runtime, "_print_startup_status", _capture_startup_output)

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
    monkeypatch.setattr(runtime, "SourceIngestor", _FailingIngestor)
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
    monkeypatch.setattr(runtime, "SourceIngestor", _FetchFailingIngestor)
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(runtime, "_build_source_connector", lambda _runtime: SimpleNamespace(source_type="fixture"))

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
    monkeypatch.setattr(runtime, "SourceIngestor", _StoreFailingIngestor)
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(runtime, "_build_source_connector", lambda _runtime: SimpleNamespace(source_type="fixture"))

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
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: events.append((event, payload)))
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "answer_commit_persistence", lambda **kwargs: None)

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

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _pipeline)

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

    def _fake_execute(*, runtime: dict[str, object], store, background: bool = False, ingestion_request_id: str = ""):
        del runtime, store
        return {"ok": True, "status": "completed", "payload": {"background": background, "stored_count": 2, "ingestion_request_id": ingestion_request_id}}

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(runtime, "_execute_source_ingestion", _fake_execute)

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
    monkeypatch.setattr(runtime, "store_doc", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "generate_reflection_yaml", lambda *args, **kwargs: "claims: []")
    monkeypatch.setattr(runtime, "persist_promoted_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(runtime, "answer_commit_persistence", lambda **kwargs: None)

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

    monkeypatch.setattr(runtime, "_poll_background_source_ingestion", _poll)

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
