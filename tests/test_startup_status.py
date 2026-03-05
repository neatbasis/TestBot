from __future__ import annotations

from testbot.sat_chatbot_memory_v2 import _print_startup_status


def test_startup_status_prints_yellow_install_warning_when_ha_unavailable(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": "in_memory",
    }

    _print_startup_status(
        requested_mode="auto",
        effective_mode="cli",
        daemon_mode=False,
        runtime=runtime,
        ha_error="Missing HA_API_SECRET",
        fallback_reason="satellite connection is unavailable",
    )

    output = capsys.readouterr().out
    assert "Install warning [YELLOW]" in output


def test_startup_status_prints_green_install_warning_when_ha_available(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": "in_memory",
    }

    _print_startup_status(
        requested_mode="auto",
        effective_mode="satellite",
        daemon_mode=False,
        runtime=runtime,
        ha_error=None,
    )

    output = capsys.readouterr().out
    assert "Install warning [GREEN]" in output



def test_startup_status_prints_degraded_cli_fallback_note_and_continuity_message(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": "in_memory",
    }

    _print_startup_status(
        requested_mode="satellite",
        effective_mode="cli",
        daemon_mode=False,
        runtime=runtime,
        ha_error="Missing HA_API_SECRET",
        fallback_reason="satellite connection is unavailable",
    )

    output = capsys.readouterr().out
    assert "CLI fallback will be used unless --daemon is set" in output
    assert "Continuity: memory cards are shared across interfaces in-process via one vector store." in output


def test_startup_status_includes_requested_and_effective_modes_for_fallback(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": "in_memory",
    }

    _print_startup_status(
        requested_mode="satellite",
        effective_mode="cli",
        daemon_mode=False,
        runtime=runtime,
        ha_error="Missing HA_API_SECRET",
        fallback_reason="satellite connection is unavailable",
    )

    output = capsys.readouterr().out
    assert "Selected mode: cli (requested=satellite, fallback reason=satellite connection is unavailable, daemon=False)" in output


def test_startup_status_prints_active_memory_backend(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": "elasticsearch",
    }

    _print_startup_status(
        requested_mode="auto",
        effective_mode="cli",
        daemon_mode=False,
        runtime=runtime,
        ha_error="Missing HA_API_SECRET",
        fallback_reason="satellite connection is unavailable",
    )

    output = capsys.readouterr().out
    assert "Memory backend: elasticsearch" in output
