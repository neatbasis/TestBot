from __future__ import annotations

from testbot.sat_chatbot_memory_v2 import CapabilitySnapshot, RuntimeCapabilityStatus, _print_startup_status


def _snapshot(*, effective_mode: str | None, ha_error: str | None, ollama_error: str | None, fallback_reason: str | None = None, memory_backend: str = "in_memory") -> CapabilitySnapshot:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text",
        "ha_api_url": "http://localhost:8123",
        "ha_api_secret": "secret",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": memory_backend,
    }
    return CapabilitySnapshot(
        runtime=runtime,
        requested_mode="auto",
        daemon_mode=False,
        effective_mode=effective_mode,
        fallback_reason=fallback_reason,
        exit_reason=None,
        ha_error=ha_error,
        ollama_error=ollama_error,
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=ollama_error is None,
            ha_available=ha_error is None,
            effective_mode=effective_mode or "unavailable",
            requested_mode="auto",
            daemon_mode=False,
            fallback_reason=fallback_reason,
            memory_backend=memory_backend,
            debug_enabled=False,
            text_clarification_available=(effective_mode or "unavailable") in {"cli", "satellite"},
            satellite_ask_available=(ha_error is None and (effective_mode or "unavailable") == "satellite"),
        ),
    )


def test_startup_status_prints_yellow_install_warning_when_ha_unavailable(capsys) -> None:
    _print_startup_status(
        snapshot=_snapshot(
            effective_mode="cli",
            ha_error="Missing HA_API_SECRET",
            ollama_error=None,
            fallback_reason="satellite connection is unavailable",
        )
    )

    output = capsys.readouterr().out
    assert "Install warning [YELLOW]" in output


def test_startup_status_prints_green_install_warning_when_ha_available(capsys) -> None:
    _print_startup_status(
        snapshot=_snapshot(
            effective_mode="satellite",
            ha_error=None,
            ollama_error=None,
        )
    )

    output = capsys.readouterr().out
    assert "Install warning [GREEN]" in output


def test_startup_status_prints_degraded_cli_fallback_note_and_continuity_message(capsys) -> None:
    _print_startup_status(
        snapshot=_snapshot(
            effective_mode="cli",
            ha_error="Missing HA_API_SECRET",
            ollama_error=None,
            fallback_reason="satellite connection is unavailable",
        )
    )

    output = capsys.readouterr().out
    assert "CLI fallback will be used unless --daemon is set" in output
    assert "Continuity: memory cards are shared across interfaces in-process via one vector store." in output


def test_startup_status_includes_requested_and_effective_modes_for_fallback(capsys) -> None:
    snapshot = _snapshot(
        effective_mode="cli",
        ha_error="Missing HA_API_SECRET",
        ollama_error=None,
        fallback_reason="satellite connection is unavailable",
    )
    snapshot = CapabilitySnapshot(
        runtime=snapshot.runtime,
        requested_mode="satellite",
        daemon_mode=snapshot.daemon_mode,
        effective_mode=snapshot.effective_mode,
        fallback_reason=snapshot.fallback_reason,
        exit_reason=snapshot.exit_reason,
        ha_error=snapshot.ha_error,
        ollama_error=snapshot.ollama_error,
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=snapshot.runtime_capability_status.ollama_available,
            ha_available=snapshot.runtime_capability_status.ha_available,
            effective_mode=snapshot.runtime_capability_status.effective_mode,
            requested_mode="satellite",
            daemon_mode=snapshot.runtime_capability_status.daemon_mode,
            fallback_reason=snapshot.runtime_capability_status.fallback_reason,
            memory_backend=snapshot.runtime_capability_status.memory_backend,
            debug_enabled=snapshot.runtime_capability_status.debug_enabled,
            text_clarification_available=snapshot.runtime_capability_status.text_clarification_available,
            satellite_ask_available=snapshot.runtime_capability_status.satellite_ask_available,
        ),
    )

    _print_startup_status(snapshot=snapshot)

    output = capsys.readouterr().out
    assert "Selected mode: cli (requested=satellite, fallback reason=satellite connection is unavailable, daemon=False)" in output


def test_startup_status_prints_active_memory_backend(capsys) -> None:
    _print_startup_status(
        snapshot=_snapshot(
            effective_mode="cli",
            ha_error="Missing HA_API_SECRET",
            ollama_error=None,
            fallback_reason="satellite connection is unavailable",
            memory_backend="elasticsearch",
        )
    )

    output = capsys.readouterr().out
    assert "Memory backend: elasticsearch" in output


def test_startup_status_prints_ollama_unavailable_guidance(capsys) -> None:
    _print_startup_status(
        snapshot=_snapshot(
            effective_mode="unavailable",
            ha_error=None,
            ollama_error="Configured chat model 'llama3.1:latest' is not installed",
        )
    )

    output = capsys.readouterr().out
    assert "Ollama: unavailable" in output
    assert "Install warning [RED]" in output
    assert "pull required models" in output
