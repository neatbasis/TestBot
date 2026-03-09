from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from urllib.error import HTTPError

from testbot.sat_chatbot_memory_v2 import CLARIFY_ANSWER, _parse_args, _resolve_mode, resolve_turn_intent
from testbot import sat_chatbot_memory_v2 as runtime


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.mode == "auto"
    assert args.daemon is False


def test_parse_args_satellite_daemon() -> None:
    args = _parse_args(["--mode", "satellite", "--daemon"])
    assert args.mode == "satellite"
    assert args.daemon is True




def test_parse_args_debug_verbose_defaults_to_none() -> None:
    args = _parse_args([])
    assert args.debug_verbose is None


def test_parse_args_debug_verbose_opt_in() -> None:
    args = _parse_args(["--debug-verbose"])
    assert args.debug_verbose is True


def test_parse_args_debug_verbose_opt_out() -> None:
    args = _parse_args(["--no-debug-verbose"])
    assert args.debug_verbose is False


def test_read_runtime_env_debug_verbose_defaults_false(monkeypatch) -> None:
    monkeypatch.delenv("TESTBOT_DEBUG_VERBOSE", raising=False)
    runtime_env = runtime._read_runtime_env()
    assert runtime_env["debug_verbose"] is False


def test_read_runtime_env_debug_verbose_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("TESTBOT_DEBUG_VERBOSE", "1")
    runtime_env = runtime._read_runtime_env()
    assert runtime_env["debug_verbose"] is True

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
    runtime_overrides: dict | None = None,
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


def test_background_source_ingestion_start_and_poll_completion(monkeypatch) -> None:
    logs: list[tuple[str, dict[str, object]]] = []

    def _fake_execute(*, runtime: dict[str, object], store, background: bool = False):
        del runtime, store
        return {"ok": True, "status": "completed", "payload": {"background": background, "stored_count": 2}}

    monkeypatch.setattr(runtime, "append_session_log", lambda event, payload: logs.append((event, payload)))
    monkeypatch.setattr(runtime, "_execute_source_ingestion", _fake_execute)

    rt = {"source_ingest_background_future": None, "source_ingest_background_in_progress": False}
    started = runtime._start_background_source_ingestion(runtime=rt, store=object())

    assert started["started"] is True
    assert logs[0][0] == "source_ingest_background_started"

    while True:
        polled = runtime._poll_background_source_ingestion(runtime=rt)
        if polled and polled.get("status") != "running":
            break

    assert polled is not None
    assert polled["ok"] is True
    assert rt["source_ingest_background_in_progress"] is False
    assert logs[-1][0] == "source_ingest_completed"
    assert logs[-1][1]["background"] is True


def test_read_runtime_env_sync_retry_wait_budget_defaults(monkeypatch) -> None:
    monkeypatch.delenv("SOURCE_INGEST_SYNC_RETRY_WAIT_BUDGET_SECONDS", raising=False)
    runtime_env = runtime._read_runtime_env()
    assert runtime_env["source_ingest_sync_retry_wait_budget_seconds"] == 0.15


def test_run_retrieval_with_optional_sync_retry_only_when_async_continuation_off(monkeypatch) -> None:
    call_counter = {"count": 0}

    def _retrieve_once():
        call_counter["count"] += 1
        return object(), []

    monkeypatch.setattr(runtime, "_bounded_wait_for_sync_retrieval_retry", lambda **_kwargs: 0.01)

    _state, docs, retry = runtime._run_retrieval_with_optional_sync_retry(
        retrieve_once=_retrieve_once,
        source_ingest_async_continuation=False,
        wait_budget_seconds=0.05,
    )

    assert docs == []
    assert call_counter["count"] == 2
    assert retry["attempted"] is True
    assert retry["reason"] == "sync_retry_completed"


def test_run_retrieval_with_optional_sync_retry_skips_second_pass_when_async_continuation_on(monkeypatch) -> None:
    call_counter = {"count": 0}

    def _retrieve_once():
        call_counter["count"] += 1
        return object(), []

    monkeypatch.setattr(runtime, "_bounded_wait_for_sync_retrieval_retry", lambda **_kwargs: 0.5)

    _state, docs, retry = runtime._run_retrieval_with_optional_sync_retry(
        retrieve_once=_retrieve_once,
        source_ingest_async_continuation=True,
        wait_budget_seconds=0.05,
    )

    assert docs == []
    assert call_counter["count"] == 1
    assert retry["attempted"] is False
    assert retry["reason"] == "async_continuation_enabled"


def test_run_retrieval_with_optional_sync_retry_uses_second_pass_results_deterministically(monkeypatch) -> None:
    sequence = [[], [(object(), 0.91)]]

    def _retrieve_once():
        docs = sequence.pop(0)
        return object(), docs

    monkeypatch.setattr(runtime, "_bounded_wait_for_sync_retrieval_retry", lambda **_kwargs: 0.02)

    _state, docs, retry = runtime._run_retrieval_with_optional_sync_retry(
        retrieve_once=_retrieve_once,
        source_ingest_async_continuation=False,
        wait_budget_seconds=0.05,
    )

    assert len(docs) == 1
    assert retry["attempted"] is True
    assert retry["reason"] == "sync_retry_completed"
