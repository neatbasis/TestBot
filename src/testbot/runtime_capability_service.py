"""Runtime capability authority service.

Owns capability probing, mode resolution, and capability snapshot construction.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from collections.abc import Callable
from typing import Protocol
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from homeassistant_api import Client

from testbot.adapters.ask_gateway import normalize_ha_rest_url
from testbot.interaction_policy import (
    COLLECT_TURN_INPUT_INTENT,
    InteractionPolicyRequest,
    ResolutionSource,
    resolve_channel_context,
)
from testbot.interaction_standards import InteractionRequirements


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityStatusData:
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
    ask_runtime_state: str = "terminal_only"
    available_ask_channels: tuple[str, ...] = ("terminal",)
    primary_ask_channel: str | None = "terminal"
    ask_runtime_reason: str | None = None
    resolved_channel: str | None = "terminal"
    resolution_source: ResolutionSource = "named_fallback"
    fallback_used: bool = True
    resolution_fallback_reason: str | None = "policy_override_recent_unavailable"


@dataclass(frozen=True, slots=True)
class CapabilitySnapshotData:
    requested_mode: str
    daemon_mode: bool
    effective_mode: str | None
    fallback_reason: str | None
    exit_reason: str | None
    ha_error: str | None
    ollama_error: str | None
    runtime_capability_status: RuntimeCapabilityStatusData


class RuntimeConfigView(Protocol):
    def __getitem__(self, key: str) -> object: ...

    def get(self, key: str, default: object | None = None) -> object: ...


def ha_connection_error(
    api_url: str,
    token: str,
    entity_id: str,
    *,
    client_factory: type[Client] = Client,
) -> str | None:
    if not token:
        return "Missing HA_API_TOKEN"
    if not entity_id:
        return "Missing HA_SATELLITE_ENTITY_ID"
    try:
        with client_factory(normalize_ha_rest_url(api_url), token):
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
        with urlopen(request, timeout=3.0) as resp:  # noqa: S310
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

    if requested_mode == "auto" and ha_error is not None and daemon_mode:
        return None, None, f"Home Assistant is unavailable: {ha_error}"

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
    runtime: RuntimeConfigView,
    ha_error: str | None,
    ollama_error: str | None,
) -> RuntimeCapabilityStatusData:
    effective = effective_mode or "unavailable"
    is_unavailable = effective == "unavailable"
    daemon_without_satellite_channel = (
        requested_mode == "satellite"
        and daemon_mode
        and ha_error is not None
    )
    satellite_channel_operational = effective == "satellite" and ha_error is None
    terminal_channel_operational = effective == "cli" or (
        effective == "satellite" and not daemon_mode
    )
    available_ask_channels = tuple(
        channel
        for channel, available in (
            ("terminal", terminal_channel_operational),
            ("satellite", satellite_channel_operational),
        )
        if available
    )
    ask_runtime_available = bool(available_ask_channels)
    if daemon_without_satellite_channel:
        ask_runtime_state = "misconfigured"
        ask_runtime_reason = "daemon_requested_without_usable_ask_channel"
    elif not ask_runtime_available:
        ask_runtime_state = "unavailable"
        if ollama_error is not None:
            ask_runtime_reason = "ollama_unavailable"
        elif ha_error is not None:
            ask_runtime_reason = "home_assistant_unavailable"
        elif is_unavailable:
            ask_runtime_reason = "effective_mode_unavailable"
        else:
            ask_runtime_reason = "no_usable_ask_channel"
    elif set(available_ask_channels) == {"terminal", "satellite"}:
        ask_runtime_state = "multi_channel"
        ask_runtime_reason = None
    elif available_ask_channels == ("satellite",):
        ask_runtime_state = "satellite_available"
        ask_runtime_reason = None
    else:
        ask_runtime_state = "terminal_only"
        ask_runtime_reason = None

    primary_ask_channel = available_ask_channels[0] if available_ask_channels else None
    can_text_clarify = ask_runtime_available
    can_satellite_ask = "satellite" in available_ask_channels
    allowed_channels = frozenset({"satellite", "cli"} if effective == "satellite" and ha_error is None else {"cli"})
    interaction_policy = InteractionPolicyRequest(
        intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="satellite" if effective == "satellite" else "cli",
        task_flow_context="memory_chat_loop",
        interaction_requirements=InteractionRequirements(),
        policy_id="runtime.capability_status.ask_input.v1",
    )
    channel_resolution = resolve_channel_context(
        interaction_policy=interaction_policy,
        allowed_channels=allowed_channels,
    )
    resolved_channel = None
    if ask_runtime_available:
        resolved_channel = (
            "satellite"
            if channel_resolution.resolved_channel_context == "satellite" and can_satellite_ask
            else "terminal"
        )
    return RuntimeCapabilityStatusData(
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
        ask_runtime_state=ask_runtime_state,
        available_ask_channels=available_ask_channels,
        primary_ask_channel=primary_ask_channel,
        ask_runtime_reason=ask_runtime_reason,
        resolved_channel=resolved_channel,
        resolution_source=channel_resolution.resolution_source,
        fallback_used=channel_resolution.fallback_used,
        resolution_fallback_reason=channel_resolution.fallback_reason,
    )


def build_capability_snapshot(
    *,
    requested_mode: str,
    daemon_mode: bool,
    runtime: RuntimeConfigView,
    ha_connection_error_fn: Callable[[str, str, str], str | None] = ha_connection_error,
    ollama_connection_error_fn: Callable[..., str | None] = ollama_connection_error,
) -> CapabilitySnapshotData:
    ha_error = ha_connection_error_fn(
        str(runtime["ha_base_url"]),
        str(runtime["ha_api_token"]),
        str(runtime["ha_satellite_entity_id"]),
    )
    ollama_error = ollama_connection_error_fn(
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

    return CapabilitySnapshotData(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        effective_mode=effective_mode,
        fallback_reason=fallback_reason,
        exit_reason=exit_reason,
        ha_error=ha_error,
        ollama_error=ollama_error,
        runtime_capability_status=runtime_capability_status,
    )


__all__ = [
    "CapabilitySnapshotData",
    "RuntimeCapabilityStatusData",
    "build_capability_snapshot",
    "build_runtime_capability_status",
    "ha_connection_error",
    "ollama_connection_error",
    "resolve_effective_mode",
    "resolve_mode",
    "validate_ollama_base_url",
]
