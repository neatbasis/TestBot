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
            "print(config.HA_API_SECRET); "
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
            "HA_API_SECRET": "ha-test-supersecret-token",
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
