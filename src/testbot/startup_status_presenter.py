from __future__ import annotations

from collections.abc import Sequence


def render_startup_status_lines(*, snapshot: object) -> list[str]:
    runtime = getattr(snapshot, "runtime")
    effective_mode = getattr(snapshot, "effective_mode") or "unavailable"
    requested_mode = getattr(snapshot, "requested_mode")
    daemon_mode = getattr(snapshot, "daemon_mode")
    fallback_reason = getattr(snapshot, "fallback_reason")
    ollama_error = getattr(snapshot, "ollama_error")
    ha_error = getattr(snapshot, "ha_error")
    capability_status = getattr(snapshot, "runtime_capability_status")

    lines = ["=== TestBot startup status ==="]
    if fallback_reason:
        lines.append(
            "Selected mode: "
            f"{effective_mode} (requested={requested_mode}, "
            f"fallback reason={fallback_reason}, daemon={daemon_mode})"
        )
    else:
        lines.append(f"Selected mode: {effective_mode} (requested={requested_mode}, daemon={daemon_mode})")

    lines.append(
        f"Ollama endpoint: {runtime['ollama_base_url']} "
        f"chat_model={runtime['ollama_model']} embed_model={runtime['ollama_embedding_model']}"
    )
    if ollama_error:
        lines.append(f"Ollama: unavailable ({ollama_error})")
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
    debug_mode = "enabled" if getattr(capability_status, "debug_enabled") else "disabled"
    debug_verbose = "enabled" if getattr(capability_status, "debug_verbose") else "disabled"
    lines.append(
        f"Debug tracing: {debug_mode} (TESTBOT_DEBUG), verbose payloads: {debug_verbose} (TESTBOT_DEBUG_VERBOSE/--debug-verbose)"
    )

    if ha_error:
        lines.append(f"Home Assistant: unavailable ({ha_error})")
        lines.append(
            "Install warning [YELLOW]: Home Assistant capability is degraded; configure HA_API_TOKEN and HA_SATELLITE_ENTITY_ID to enable satellite mode."
        )
        lines.append(
            "Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set."
        )
    else:
        lines.append(
            f"Home Assistant: available ({runtime['ha_api_url']}, entity={runtime['ha_satellite_entity_id']})"
        )
        lines.append(
            "Install warning [GREEN]: Home Assistant capability is active; keep Home Assistant credentials configured when reinstalling or reprovisioning."
        )
        lines.append("Developer note: satellite ask/speak loop is enabled.")

    lines.append("Continuity: memory cards are shared across interfaces in-process via one vector store.")
    lines.append("==============================")
    return lines


def print_startup_status(*, snapshot: object) -> None:
    for line in render_startup_status_lines(snapshot=snapshot):
        print(line)


__all__ = ["print_startup_status", "render_startup_status_lines"]
