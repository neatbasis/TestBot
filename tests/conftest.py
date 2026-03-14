from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from testbot.config import Config


def require_live_smoke_config(*, suite_name: str, required_fields: tuple[str, ...]) -> None:
    config = Config.from_env()
    missing_fields = [
        field_name
        for field_name in required_fields
        if not str(getattr(config, field_name, "")).strip()
    ]
    if missing_fields:
        formatted = ", ".join(missing_fields)
        pytest.skip(
            f"Set non-empty configuration values for {formatted} to run {suite_name}",
            allow_module_level=True,
        )
