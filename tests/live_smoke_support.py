from __future__ import annotations

import pytest

from testbot.config import Config


def require_live_smoke_config(*, suite_name: str, required_fields: tuple[str, ...]) -> None:
    """Skip module-level live smoke suites when required env config is absent.

    The skip reason is intentionally explicit so contributors understand both why
    the suite was skipped and what behavior is expected once configuration is
    provided.
    """

    config = Config.from_env()
    missing_fields = [
        field_name
        for field_name in required_fields
        if not str(getattr(config, field_name, "")).strip()
    ]
    if missing_fields:
        formatted = ", ".join(missing_fields)
        pytest.skip(
            (
                "Live smoke suite skipped because required environment variables are "
                f"missing or empty: {formatted}. "
                "Expected behavior: when these variables are set to reachable services, "
                "this suite runs end-to-end integration checks against real dependencies."
            ),
            allow_module_level=True,
        )
