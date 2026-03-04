from __future__ import annotations

from testbot.sat_chatbot_memory_v2 import _print_startup_status


def test_startup_status_prints_yellow_install_warning_when_ha_unavailable(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }

    _print_startup_status(selected_mode="cli", daemon_mode=False, runtime=runtime, ha_error="Missing HA_API_SECRET")

    output = capsys.readouterr().out
    assert "Install warning [YELLOW]" in output


def test_startup_status_prints_green_install_warning_when_ha_available(capsys) -> None:
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ha_api_url": "http://localhost:8123",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
    }

    _print_startup_status(selected_mode="satellite", daemon_mode=False, runtime=runtime, ha_error=None)

    output = capsys.readouterr().out
    assert "Install warning [GREEN]" in output

