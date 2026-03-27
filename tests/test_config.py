from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_config_loads_from_process_environment() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "from testbot.config import Config; "
            "config = Config.from_env(); "
            "print(config.HA_API_TOKEN); "
            "print(config.HA_SATELLITE_ENTITY_ID); "
            "print(config.OLLAMA_MODEL); "
            "print(config.X_OLLAMA_KEY)"
        ),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={
            "HA_API_TOKEN": "ha-test-supersecret-token",
            "HA_SATELLITE_ENTITY_ID": "assist_satellite.test",
            "OLLAMA_MODEL": "custom-model",
            "X_OLLAMA_KEY": "x-ollama-test-key",
            "PYTHONPATH": str(Path.cwd() / "src"),
            "PATH": os.environ.get("PATH", ""),
        },
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines() == [
        "ha-test-supersecret-token",
        "assist_satellite.test",
        "custom-model",
        "x-ollama-test-key",
    ]


def test_config_prefers_ha_base_url_over_ha_api_url_alias() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "from testbot.config import Config; "
            "config = Config.from_env(); "
            "print(config.HA_API_URL)"
        ),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={
            "HA_BASE_URL": "http://ha-base-url:8123",
            "HA_API_URL": "http://legacy-ha-api-url:8123",
            "PYTHONPATH": str(Path.cwd() / "src"),
            "PATH": os.environ.get("PATH", ""),
        },
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "http://ha-base-url:8123"
    assert "HA_API_URL is deprecated" not in completed.stderr


def test_config_supports_ha_api_url_alias_with_deprecation_warning() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "from testbot.config import Config; "
            "config = Config.from_env(); "
            "print(config.HA_API_URL)"
        ),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={
            "HA_API_URL": "http://legacy-ha-api-url:8123",
            "PYTHONPATH": str(Path.cwd() / "src"),
            "PATH": os.environ.get("PATH", ""),
        },
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "http://legacy-ha-api-url:8123"
    assert "HA_API_URL is deprecated for Home Assistant base URL; prefer HA_BASE_URL." in completed.stderr
