from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from homeassistant_api import Client

from testbot.adapters.ask_gateway import normalize_ha_rest_url
from testbot.adapters.memory_store_factory import normalize_memory_store_mode
from testbot.config import Config


@dataclass(frozen=True)
class RuntimeCapabilityStatus:
    ollama_available: bool
    ha_available: bool
    effective_mode: str
    requested_mode: str
    daemon_mode: bool
    fallback_reason: str | None
    memory_backend: str
    debug_enabled: bool
    debug_verbose: bool
    text_clarification_available: bool
    satellite_ask_available: bool


@dataclass(frozen=True)
class CapabilitySnapshot:
    runtime: dict[str, object]
    requested_mode: str
    daemon_mode: bool
    effective_mode: str | None
    fallback_reason: str | None
    exit_reason: str | None
    ha_error: str | None
    ollama_error: str | None
    runtime_capability_status: RuntimeCapabilityStatus


def read_runtime_env() -> dict[str, object]:
    config = Config.from_env()
    memory_store_mode = os.getenv("MEMORY_STORE_MODE", "in_memory")
    debug_verbose = os.getenv("TESTBOT_DEBUG_VERBOSE", "0") == "1"
    return {
        "ha_api_url": config.HA_API_URL,
        "ha_api_token": config.HA_API_TOKEN,
        "ha_satellite_entity_id": config.HA_SATELLITE_ENTITY_ID,
        "ollama_base_url": config.OLLAMA_BASE_URL,
        "ollama_model": config.OLLAMA_MODEL,
        "ollama_embedding_model": config.OLLAMA_EMBEDDING_MODEL,
        "x_ollama_key": config.X_OLLAMA_KEY,
        "memory_near_tie_delta": config.MEMORY_NEAR_TIE_DELTA,
        "memory_store_mode": memory_store_mode,
        "memory_store_backend": normalize_memory_store_mode(memory_store_mode),
        "elasticsearch_url": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        "elasticsearch_index": os.getenv("ELASTICSEARCH_INDEX", "testbot_memory_cards"),
        "source_ingest_enabled": config.SOURCE_INGEST_ENABLED,
        "source_connector_type": config.SOURCE_CONNECTOR_TYPE,
        "source_fixture_path": config.SOURCE_FIXTURE_PATH,
        "source_ingest_limit": config.SOURCE_INGEST_LIMIT,
        "source_ingest_cursor": config.SOURCE_INGEST_CURSOR,
        "source_markdown_path": config.SOURCE_MARKDOWN_PATH,
        "source_wikipedia_topic": config.SOURCE_WIKIPEDIA_TOPIC,
        "source_wikipedia_language": config.SOURCE_WIKIPEDIA_LANGUAGE,
        "source_arxiv_query": config.SOURCE_ARXIV_QUERY,
        "source_ingest_async_continuation": os.getenv("SOURCE_INGEST_ASYNC_CONTINUATION", "0") == "1",
        "source_ingest_background_future": None,
        "source_ingest_background_in_progress": False,
        "source_ingest_background_request_id": "",
        "debug_verbose": debug_verbose,
    }


def ha_connection_error(
    api_url: str,
    token: str,
    entity_id: str,
    *,
    client_cls=Client,
) -> str | None:
    if not token:
        return "Missing HA_API_TOKEN"
    if not entity_id:
        return "Missing HA_SATELLITE_ENTITY_ID"
    try:
        with client_cls(normalize_ha_rest_url(api_url), token):
            return None
    except Exception as exc:  # pragma: no cover - network/credential dependent
        return f"{type(exc).__name__}: {exc}"


def validate_ollama_base_url(base_url: str) -> str | None:
    parsed = urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return f"Invalid OLLAMA_BASE_URL '{base_url}'; must be full http(s) URL"
    return None


def ollama_connection_error(
    base_url: str,
    chat_model: str,
    embedding_model: str,
    *,
    x_ollama_key: str | None = None,
    urlopen_fn=urlopen,
) -> str | None:
    def _model_aliases(model_name: str) -> set[str]:
        trimmed = model_name.strip()
        if not trimmed:
            return set()
        if ":" in trimmed:
            base_name, _, tag = trimmed.rpartition(":")
            if tag == "latest":
                return {trimmed, base_name}
            return {trimmed}
        return {trimmed, f"{trimmed}:latest"}

    base_url_error = validate_ollama_base_url(base_url)
    if base_url_error is not None:
        return base_url_error

    tags_url = urljoin(base_url.rstrip("/") + "/", "api/tags")
    request = Request(tags_url)
    if x_ollama_key:
        request.add_header("X-Ollama-Key", x_ollama_key)

    try:
        with urlopen_fn(request, timeout=3.0) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
    except URLError as exc:  # pragma: no cover - network dependent
        return f"Cannot reach Ollama endpoint {base_url}: {type(exc.reason).__name__}: {exc.reason}"
    except Exception as exc:  # pragma: no cover - network dependent
        return f"Cannot reach Ollama endpoint {base_url}: {type(exc).__name__}: {exc}"

    models = payload.get("models", []) if isinstance(payload, dict) else []
    available = {
        str(item.get("model") or item.get("name") or "")
        for item in models
        if isinstance(item, dict)
    }
    if available.isdisjoint(_model_aliases(chat_model)):
        return (
            f"Configured chat model '{chat_model}' is not installed on Ollama. "
            f"Run: ollama pull {chat_model}"
        )
    if available.isdisjoint(_model_aliases(embedding_model)):
        return (
            f"Configured embedding model '{embedding_model}' is not installed on Ollama. "
            f"Run: ollama pull {embedding_model}"
        )
    return None


def resolve_mode(requested_mode: str, ha_error: str | None) -> str:
    if requested_mode == "auto":
        return "satellite" if ha_error is None else "cli"
    return requested_mode


def resolve_effective_mode(
    *,
    requested_mode: str,
    daemon_mode: bool,
    ha_error: str | None,
    ollama_error: str | None,
) -> tuple[str | None, str | None, str | None]:
    if ollama_error is not None:
        return None, None, f"Ollama is unavailable: {ollama_error}"

    if requested_mode == "auto" and ha_error is not None:
        if daemon_mode:
            return None, None, f"Home Assistant is unavailable: {ha_error}"
        return "cli", "satellite connection is unavailable", None

    selected_mode = resolve_mode(requested_mode, ha_error)
    if selected_mode == "satellite" and ha_error is not None:
        if daemon_mode:
            return None, None, f"Home Assistant is unavailable: {ha_error}"
        return "cli", "satellite connection is unavailable", None
    return selected_mode, None, None


def build_runtime_capability_status(
    *,
    requested_mode: str,
    effective_mode: str | None,
    daemon_mode: bool,
    fallback_reason: str | None,
    runtime: dict[str, object],
    ha_error: str | None,
    ollama_error: str | None,
) -> RuntimeCapabilityStatus:
    effective = effective_mode or "unavailable"
    can_text_clarify = effective in {"cli", "satellite"}
    can_satellite_ask = ha_error is None and effective == "satellite"
    return RuntimeCapabilityStatus(
        ollama_available=ollama_error is None,
        ha_available=ha_error is None,
        effective_mode=effective,
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        fallback_reason=fallback_reason,
        memory_backend=str(runtime.get("memory_store_backend", "unknown")),
        debug_enabled=os.getenv("TESTBOT_DEBUG", "0") == "1",
        debug_verbose=bool(runtime.get("debug_verbose", False)),
        text_clarification_available=can_text_clarify,
        satellite_ask_available=can_satellite_ask,
    )


def build_capability_snapshot(*, requested_mode: str, daemon_mode: bool, runtime: dict[str, object]) -> CapabilitySnapshot:
    ha_error = ha_connection_error(
        str(runtime["ha_api_url"]),
        str(runtime["ha_api_token"]),
        str(runtime["ha_satellite_entity_id"]),
    )
    ollama_error = ollama_connection_error(
        str(runtime["ollama_base_url"]),
        str(runtime["ollama_model"]),
        str(runtime["ollama_embedding_model"]),
        x_ollama_key=str(runtime.get("x_ollama_key") or ""),
    )

    effective_mode, fallback_reason, exit_reason = resolve_effective_mode(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        ha_error=ha_error,
        ollama_error=ollama_error,
    )

    runtime_capability_status = build_runtime_capability_status(
        requested_mode=requested_mode,
        effective_mode=effective_mode,
        daemon_mode=daemon_mode,
        fallback_reason=fallback_reason,
        runtime=runtime,
        ha_error=ha_error,
        ollama_error=ollama_error,
    )

    return CapabilitySnapshot(
        runtime=runtime,
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        effective_mode=effective_mode,
        fallback_reason=fallback_reason,
        exit_reason=exit_reason,
        ha_error=ha_error,
        ollama_error=ollama_error,
        runtime_capability_status=runtime_capability_status,
    )
