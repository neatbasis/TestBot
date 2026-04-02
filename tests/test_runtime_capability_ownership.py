from __future__ import annotations

from testbot.runtime_capability_service import (
    AskRuntimeStatusData,
    CapabilitySnapshotData,
    RuntimeCapabilityStatusData,
)
from testbot.startup_status_presenter import render_startup_status_lines


def _runtime_env() -> dict[str, object]:
    return {
        "ha_base_url": "http://localhost:8123",
        "ha_api_token": "",
        "ha_satellite_entity_id": "assist_satellite.office",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text:latest",
        "memory_store_backend": "in_memory",
    }


def test_startup_status_prefers_authoritative_ask_runtime_representation() -> None:
    runtime_status = RuntimeCapabilityStatusData(
        ollama_available=True,
        ha_available=True,
        effective_mode="satellite",
        requested_mode="satellite",
        daemon_mode=False,
        fallback_reason=None,
        memory_backend="in_memory",
        debug_enabled=False,
        debug_verbose=False,
        ask_runtime=AskRuntimeStatusData(
            ask_runtime_state="unavailable",
            available_ask_channels=(),
            primary_ask_channel=None,
            ask_runtime_reason="no_usable_ask_channel",
        ),
        # Intentionally contradictory legacy booleans; presenter should ignore these.
        text_clarification_available=True,
        satellite_ask_available=True,
    )
    snapshot = CapabilitySnapshotData(
        runtime=_runtime_env(),
        requested_mode="satellite",
        daemon_mode=False,
        effective_mode="satellite",
        fallback_reason=None,
        exit_reason=None,
        ha_error=None,
        ollama_error=None,
        runtime_capability_status=runtime_status,
    )

    lines = render_startup_status_lines(snapshot=snapshot)
    joined = "\n".join(lines)

    assert "Ask-backed turn input: unavailable" in joined
    assert "state=unavailable, channels=none" in joined
    assert "Satellite Ask channel: unavailable." in joined
