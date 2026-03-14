from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def pytest_configure(config: pytest.Config) -> None:
    """Auto-enable live smoke gating when those tests are explicitly targeted."""
    explicit_args = tuple(str(arg) for arg in config.invocation_params.args)
    requested_live_smoke_file = any(
        "test_live_smoke_" in arg and arg.endswith(".py") for arg in explicit_args
    )
    is_live_smoke_enabled = os.getenv("TESTBOT_ENABLE_LIVE_SMOKE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if requested_live_smoke_file and not is_live_smoke_enabled:
        os.environ["TESTBOT_ENABLE_LIVE_SMOKE"] = "1"
