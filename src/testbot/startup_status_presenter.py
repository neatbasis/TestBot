"""Startup status presenter.

Owns presentation of startup capability state; does not probe capabilities.
"""

from __future__ import annotations

from typing import Protocol, TypedDict


class StartupRuntimeView(TypedDict):
    ollama_base_url: str
    ollama_model: str
    ollama_embedding_model: str
    memory_store_backend: str
    ha_base_url: str
    ha_satellite_entity_id: str


class RuntimeCapabilityStatusView(Protocol):
    debug_enabled: bool
    debug_verbose: bool
    text_clarification_available: bool
    satellite_ask_available: bool
    ask_runtime_state: str
    available_ask_channels: tuple[str, ...]
    primary_ask_channel: str | None
    ask_runtime_reason: str | None


class CapabilitySnapshotView(Protocol):
    """Typed read-model used by startup status presentation only."""

    runtime: StartupRuntimeView
    effective_mode: str | None
    requested_mode: str
    daemon_mode: bool
    fallback_reason: str | None
    ollama_error: str | None
    ha_error: str | None
    runtime_capability_status: RuntimeCapabilityStatusView


def render_startup_status_lines(*, snapshot: CapabilitySnapshotView) -> list[str]:
    runtime = snapshot.runtime
    effective_mode = snapshot.effective_mode or "unavailable"

    lines = ["=== TestBot startup status ==="]
    if snapshot.fallback_reason:
        lines.append(
            "Selected mode: "
            f"{effective_mode} (requested={snapshot.requested_mode}, "
            f"fallback reason={snapshot.fallback_reason}, daemon={snapshot.daemon_mode})"
        )
    else:
        lines.append(
            f"Selected mode: {effective_mode} (requested={snapshot.requested_mode}, daemon={snapshot.daemon_mode})"
        )

    lines.append(
        f"Ollama endpoint: {runtime['ollama_base_url']} "
        f"chat_model={runtime['ollama_model']} embed_model={runtime['ollama_embedding_model']}"
    )
    if snapshot.ollama_error:
        lines.append(f"Ollama: unavailable ({snapshot.ollama_error})")
        lines.append(
            "Install warning [RED]: Ollama capability is unavailable; verify OLLAMA_BASE_URL and pull required models before restarting."
        )
        lines.append(
            "Developer note: runtime will exit early because model and embedding checks are required at startup."
        )
    else:
        lines.append("Ollama: available (chat + embedding models verified)")
        lines.append(
            "Install warning [GREEN]: Ollama capability is active; keep OLLAMA_MODEL and OLLAMA_EMBEDDING_MODEL provisioned."
        )

    lines.append(f"Memory backend: {runtime['memory_store_backend']}")
    source_ingest_enabled = bool(runtime.get("source_ingest_enabled", False))
    source_connector = str(runtime.get("source_connector_type") or "none").strip().lower() or "none"
    source_selection_source = str(runtime.get("source_ingest_selection_source") or "environment").strip().lower()
    source_selection_mode = str(runtime.get("source_ingest_selection_mode") or source_selection_source).strip().lower()
    source_reference_key = str(runtime.get("source_ingest_reference_key") or "").strip()
    source_freeform_request = str(runtime.get("source_ingest_freeform_request") or "").strip()
    selection_details = [f"mode={source_selection_mode}", f"selected_via={source_selection_source}"]
    if source_reference_key:
        selection_details.append(f"reference={source_reference_key}")
    if source_freeform_request:
        selection_details.append(f"freeform='{source_freeform_request}'")
    selection_detail_text = ", ".join(selection_details)
    if source_ingest_enabled:
        lines.append(
            f"Source ingestion: enabled (connector={source_connector}, {selection_detail_text})"
        )
    else:
        lines.append(
            f"Source ingestion: disabled ({selection_detail_text})"
        )
    ask_runtime_state = getattr(snapshot.runtime_capability_status, "ask_runtime_state", "terminal_only")
    ask_channels = getattr(snapshot.runtime_capability_status, "available_ask_channels", ("terminal",))
    ask_primary = getattr(snapshot.runtime_capability_status, "primary_ask_channel", "terminal")
    ask_reason = getattr(snapshot.runtime_capability_status, "ask_runtime_reason", None)
    ask_runtime_available = "available" if snapshot.runtime_capability_status.text_clarification_available else "unavailable"
    satellite_channel_available = "available" if snapshot.runtime_capability_status.satellite_ask_available else "unavailable"
    ask_channel_text = ", ".join(ask_channels) if ask_channels else "none"
    ask_detail_segments = [f"state={ask_runtime_state}", f"channels={ask_channel_text}"]
    if ask_primary is not None:
        ask_detail_segments.append(f"primary={ask_primary}")
    if ask_reason:
        ask_detail_segments.append(f"reason={ask_reason}")
    ask_detail_text = ", ".join(ask_detail_segments)
    lines.append(
        f"Ask-backed turn input: {ask_runtime_available} (runtime requires at least one usable Ask channel: {ask_detail_text})."
    )
    lines.append(f"Satellite Ask channel: {satellite_channel_available}.")

    debug_mode = "enabled" if snapshot.runtime_capability_status.debug_enabled else "disabled"
    debug_verbose = "enabled" if snapshot.runtime_capability_status.debug_verbose else "disabled"
    lines.append(
        f"Debug tracing: {debug_mode} (TESTBOT_DEBUG), verbose payloads: {debug_verbose} (TESTBOT_DEBUG_VERBOSE/--debug-verbose)"
    )

    if snapshot.ha_error:
        lines.append(f"Home Assistant: unavailable ({snapshot.ha_error})")
        lines.append(
            "Install warning [YELLOW]: Home Assistant capability is degraded; configure HA_BASE_URL, HA_API_TOKEN, and HA_SATELLITE_ENTITY_ID to enable satellite mode."
        )
        lines.append(
            "Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set."
        )
    else:
        lines.append(
            f"Home Assistant: available ({runtime['ha_base_url']}, entity={runtime['ha_satellite_entity_id']})"
        )
        lines.append(
            "Install warning [GREEN]: Home Assistant capability is active; keep Home Assistant credentials configured when reinstalling or reprovisioning."
        )
        lines.append("Developer note: satellite ask/speak loop is enabled.")

    lines.append("Continuity: memory cards are shared across interfaces in-process via one vector store.")
    lines.append("==============================")
    return lines


def print_startup_status(*, snapshot: CapabilitySnapshotView) -> None:
    for line in render_startup_status_lines(snapshot=snapshot):
        print(line)


__all__ = ["CapabilitySnapshotView", "RuntimeCapabilityStatusView", "print_startup_status", "render_startup_status_lines"]
