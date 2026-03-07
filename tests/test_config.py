from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_config_loads_dotenv_from_testbot_home(tmp_path: Path) -> None:
    env_file = tmp_path / ".testbot" / ".env"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(
        "\n".join(
            [
                "HA_API_SECRET=ha-test-supersecret-token",
                "HA_SATELLITE_ENTITY_ID=assist_satellite.test",
                "OLLAMA_MODEL=custom-model",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    command = [
        sys.executable,
        "-c",
        (
            "from testbot.config import Config; "
            "config = Config.from_env(); "
            "print(config.HA_API_SECRET); "
            "print(config.HA_SATELLITE_ENTITY_ID); "
            "print(config.OLLAMA_MODEL)"
        ),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={
            "HOME": str(tmp_path),
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
    ]
