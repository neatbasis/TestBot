from __future__ import annotations

import os

import pytest

from tests.conftest import require_live_smoke_config

from testbot.sat_chatbot_memory_v2 import _read_runtime_env

langchain_ollama = pytest.importorskip(
    "langchain_ollama",
    reason="live_smoke requires langchain-ollama; install project dependencies first",
)

ChatOllama = langchain_ollama.ChatOllama
OllamaEmbeddings = langchain_ollama.OllamaEmbeddings

pytestmark = pytest.mark.live_smoke

require_live_smoke_config(
    suite_name="live_smoke Ollama integration tests",
    required_fields=("OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_EMBEDDING_MODEL"),
)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run live_smoke Ollama integration tests")
    return value


def _ollama_client_kwargs(runtime: dict[str, object]) -> dict[str, object]:
    if str(runtime.get("x_ollama_key", "")).strip():
        return {"client_kwargs": {"headers": {"X-Ollama-Key": str(runtime["x_ollama_key"])}}}
    return {}


def test_live_smoke_chat_ollama_invoke_returns_non_empty_response() -> None:
    _require_env("OLLAMA_BASE_URL")
    _require_env("OLLAMA_MODEL")
    _require_env("X_OLLAMA_KEY")

    runtime = _read_runtime_env()
    llm = ChatOllama(
        model=str(runtime["ollama_model"]),
        base_url=str(runtime["ollama_base_url"]),
        **_ollama_client_kwargs(runtime),
        temperature=0.0,
    )
    response = llm.invoke("Reply with exactly: ok")

    text = getattr(response, "content", str(response)).strip()
    assert text, "Expected non-empty text response from ChatOllama.invoke"


def test_live_smoke_ollama_embeddings_returns_non_empty_vector() -> None:
    _require_env("OLLAMA_BASE_URL")
    _require_env("OLLAMA_EMBEDDING_MODEL")
    _require_env("X_OLLAMA_KEY")

    runtime = _read_runtime_env()
    embeddings = OllamaEmbeddings(
        model=str(runtime["ollama_embedding_model"]),
        base_url=str(runtime["ollama_base_url"]),
        **_ollama_client_kwargs(runtime),
    )
    vector = embeddings.embed_query("smoke test")

    assert vector, "Expected non-empty embedding vector"
    assert any(float(value) != 0.0 for value in vector), "Expected embedding vector with signal"
