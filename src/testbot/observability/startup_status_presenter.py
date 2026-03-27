from __future__ import annotations

from testbot.application.services.runtime_capability_service import CapabilitySnapshot


def render_startup_status_lines(*, snapshot: CapabilitySnapshot) -> list[str]:
    runtime = snapshot.runtime
    lines = ["=== TestBot startup status ==="]
    effective_mode = snapshot.effective_mode or "unavailable"
    if snapshot.fallback_reason:
        lines.append(
            "Selected mode: "
            f"{effective_mode} (requested={snapshot.requested_mode}, "
            f"fallback reason={snapshot.fallback_reason}, daemon={snapshot.daemon_mode})"
        )
    else:
        lines.append(f"Selected mode: {effective_mode} (requested={snapshot.requested_mode}, daemon={snapshot.daemon_mode})")
    lines.append(
        f"Ollama endpoint: {runtime['ollama_base_url']} "
        f"chat_model={runtime['ollama_model']} embed_model={runtime['ollama_embedding_model']}"
    )
    if snapshot.ollama_error:
        lines.append(f"Ollama: unavailable ({snapshot.ollama_error})")
        lines.append("Install warning [RED]: Ollama capability is unavailable; verify OLLAMA_BASE_URL and pull required models before restarting.")
        lines.append("Developer note: runtime will exit early because model and embedding checks are required at startup.")
    else:
        lines.append("Ollama: available (chat + embedding models verified)")
        lines.append("Install warning [GREEN]: Ollama capability is active; keep OLLAMA_MODEL and OLLAMA_EMBEDDING_MODEL provisioned.")
    lines.append(f"Memory backend: {runtime['memory_store_backend']}")
    debug_mode = "enabled" if snapshot.runtime_capability_status.debug_enabled else "disabled"
    debug_verbose = "enabled" if snapshot.runtime_capability_status.debug_verbose else "disabled"
    lines.append(f"Debug tracing: {debug_mode} (TESTBOT_DEBUG), verbose payloads: {debug_verbose} (TESTBOT_DEBUG_VERBOSE/--debug-verbose)")
    if snapshot.ha_error:
        lines.append(f"Home Assistant: unavailable ({snapshot.ha_error})")
        lines.append("Install warning [YELLOW]: Home Assistant capability is degraded; configure HA_API_TOKEN and HA_SATELLITE_ENTITY_ID to enable satellite mode.")
        lines.append("Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set.")
    else:
        lines.append(f"Home Assistant: available ({runtime['ha_api_url']}, entity={runtime['ha_satellite_entity_id']})")
        lines.append("Install warning [GREEN]: Home Assistant capability is active; keep Home Assistant credentials configured when reinstalling or reprovisioning.")
        lines.append("Developer note: satellite ask/speak loop is enabled.")
    lines.append("Continuity: memory cards are shared across interfaces in-process via one vector store.")
    lines.append("==============================")
    return lines


def print_startup_status(*, snapshot: CapabilitySnapshot) -> None:
    for line in render_startup_status_lines(snapshot=snapshot):
        print(line)
