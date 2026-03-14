from __future__ import annotations

import os

import pytest

from testbot.config import Config

langchain_ollama = pytest.importorskip(
    "langchain_ollama",
    reason="live_smoke requires langchain-ollama; install project dependencies first",
)

ChatOllama = langchain_ollama.ChatOllama
OllamaEmbeddings = langchain_ollama.OllamaEmbeddings


pytestmark = pytest.mark.live_smoke

if os.getenv("TESTBOT_ENABLE_LIVE_SMOKE", "").strip().lower() not in {"1", "true", "yes"}:
    pytest.skip(
        "Set TESTBOT_ENABLE_LIVE_SMOKE=1 to run live_smoke Ollama integration tests",
        allow_module_level=True,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run live_smoke Ollama integration tests")
    return value


def _ollama_client_kwargs(config: Config) -> dict[str, object]:
    if config.X_OLLAMA_KEY.strip():
        return {"client_kwargs": {"headers": {"X-Ollama-Key": config.X_OLLAMA_KEY}}}
    return {}


def test_live_smoke_chat_ollama_invoke_returns_non_empty_response() -> None:
    _require_env("OLLAMA_BASE_URL")
    _require_env("OLLAMA_MODEL")

    config = Config.from_env()
    llm = ChatOllama(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL, **_ollama_client_kwargs(config), temperature=0.0)
    response = llm.invoke("Reply with exactly: ok")

    text = getattr(response, "content", str(response)).strip()
    assert text, "Expected non-empty text response from ChatOllama.invoke"


def test_live_smoke_ollama_embeddings_returns_non_empty_vector() -> None:
    _require_env("OLLAMA_BASE_URL")
    _require_env("OLLAMA_EMBEDDING_MODEL")

    config = Config.from_env()
    embeddings = OllamaEmbeddings(model=config.OLLAMA_EMBEDDING_MODEL, base_url=config.OLLAMA_BASE_URL, **_ollama_client_kwargs(config))
    vector = embeddings.embed_query("smoke test")

    assert vector, "Expected non-empty embedding vector"
    assert any(float(value) != 0.0 for value in vector), "Expected embedding vector with signal"
