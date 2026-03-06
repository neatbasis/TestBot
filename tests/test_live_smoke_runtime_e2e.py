from __future__ import annotations

from collections import deque
import os

import pytest
from langchain_ollama import ChatOllama, OllamaEmbeddings

from testbot.clock import SystemClock
from testbot.sat_chatbot_memory_v2 import (
    _read_runtime_env,
    _run_chat_loop,
    build_capability_snapshot,
)
from testbot.vector_store import build_memory_store


pytestmark = pytest.mark.live_smoke

if os.getenv("TESTBOT_ENABLE_LIVE_SMOKE", "").strip().lower() not in {"1", "true", "yes"}:
    pytest.skip(
        "Set TESTBOT_ENABLE_LIVE_SMOKE=1 to run live_smoke runtime end-to-end tests",
        allow_module_level=True,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run live_smoke runtime end-to-end tests")
    return value


def _require_live_runtime_env() -> None:
    for env_name in (
        "HA_API_URL",
        "HA_API_SECRET",
        "HA_SATELLITE_ENTITY_ID",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "OLLAMA_EMBEDDING_MODEL",
    ):
        _require_env(env_name)


def test_live_smoke_runtime_e2e_turn_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    _require_live_runtime_env()

    runtime = _read_runtime_env()
    capability_snapshot = build_capability_snapshot(
        requested_mode="auto",
        daemon_mode=False,
        runtime=runtime,
    )

    assert capability_snapshot.ha_error is None, (
        "Expected Home Assistant connectivity to be available in live smoke runtime test"
    )
    assert capability_snapshot.effective_mode == "satellite", (
        "Expected auto mode to resolve to satellite mode when HA is reachable"
    )
    assert capability_snapshot.ollama_error is None, "Expected Ollama connectivity to be available"

    llm = ChatOllama(
        model=str(runtime["ollama_model"]),
        base_url=str(runtime["ollama_base_url"]),
        temperature=0.0,
    )
    embeddings = OllamaEmbeddings(
        model=str(runtime["ollama_embedding_model"]),
        base_url=str(runtime["ollama_base_url"]),
    )
    store = build_memory_store(
        embeddings=embeddings,
        mode=str(runtime["memory_store_mode"]),
        elasticsearch_url=str(runtime["elasticsearch_url"]),
        elasticsearch_index=str(runtime["elasticsearch_index"]),
    )

    events: list[dict[str, object]] = []

    def _capture_session_log(event: str, payload: dict, *, log_path=None) -> None:  # noqa: ARG001
        events.append({"event": event, "payload": payload})

    monkeypatch.setattr("testbot.sat_chatbot_memory_v2.append_session_log", _capture_session_log)

    prompts = iter(
        [
            "Provide one short factual sentence about Earth.",
            "stop",
        ]
    )
    replies: list[str] = []

    def _read_user_utterance() -> str | None:
        return next(prompts, None)

    def _send_assistant_text(text: str) -> None:
        replies.append(text)

    try:
        _run_chat_loop(
            llm=llm,
            store=store,
            chat_history=deque(maxlen=10),
            near_tie_delta=float(runtime["memory_near_tie_delta"]),
            io_channel="cli",
            capability_status="ask_unavailable",
            capability_snapshot=capability_snapshot,
            read_user_utterance=_read_user_utterance,
            send_assistant_text=_send_assistant_text,
            clock=SystemClock(),
        )
    except Exception as exc:  # pragma: no cover - live backend dependent
        pytest.fail(f"Unexpected uncaught runtime exception during e2e live smoke turn: {type(exc).__name__}: {exc}")

    non_stop_replies = [text.strip() for text in replies if text.strip() and text.strip() != "Stopping. Bye."]
    assert non_stop_replies, "Expected at least one non-empty assistant reply from runtime pipeline"

    final_answer_mode_payload = next(
        (
            item["payload"]
            for item in events
            if item["event"] == "final_answer_mode" and isinstance(item.get("payload"), dict)
        ),
        None,
    )
    assert isinstance(final_answer_mode_payload, dict), "Expected structured final_answer_mode payload"

    required_payload_keys = {
        "mode",
        "query",
        "context_confident",
        "retrieved_docs",
        "claims",
        "provenance_types",
        "basis_statement",
    }
    assert required_payload_keys.issubset(final_answer_mode_payload), (
        "Expected final_answer_mode payload to include runtime contract keys"
    )

    assert isinstance(final_answer_mode_payload["provenance_types"], list)
    assert final_answer_mode_payload["provenance_types"], "Expected non-empty provenance type list in payload"
