from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pytest

from ha_ask.config import normalize_rest_api_url


pytestmark = pytest.mark.live_smoke

if os.getenv("TESTBOT_ENABLE_LIVE_SMOKE", "").strip().lower() not in {"1", "true", "yes"}:
    pytest.skip(
        "Set TESTBOT_ENABLE_LIVE_SMOKE=1 to run live_smoke Home Assistant integration tests",
        allow_module_level=True,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run live_smoke Home Assistant integration tests")
    return value


def _ha_get_json(*, base_url: str, token: str, endpoint: str) -> tuple[int, object]:
    url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=10.0) as response:  # noqa: S310
            status = int(response.getcode() or 0)
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        pytest.fail(
            "Home Assistant request failed with HTTP error. "
            f"url={url!r}, status={exc.code}, reason={exc.reason!r}, body={detail!r}. "
            "Check HA_API_SECRET token permissions and HA_API_URL connectivity."
        )
    except URLError as exc:
        pytest.fail(
            "Failed to connect to Home Assistant. "
            f"url={url!r}, error={exc.reason!r}. "
            "Check HA_API_URL reachability and network routing."
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        pytest.fail(
            "Home Assistant response was not valid JSON. "
            f"url={url!r}, status={status}, decode_error={exc}."
        )

    return status, payload


def test_live_smoke_home_assistant_api_root_returns_message() -> None:
    api_url = _require_env("HA_API_URL")
    token = _require_env("HA_API_SECRET")
    _require_env("HA_SATELLITE_ENTITY_ID")

    status, payload = _ha_get_json(
        base_url=normalize_rest_api_url(api_url),
        token=token,
        endpoint="/api/",
    )

    assert 200 <= status < 300, f"Expected HTTP success from /api/, got status={status}"
    assert isinstance(payload, dict), f"Expected /api/ payload to be an object, got {type(payload).__name__}"
    assert payload.get("message") == "API running.", (
        "Expected Home Assistant /api/ response to include message='API running.'"
    )


def test_live_smoke_home_assistant_states_contains_configured_satellite_entity() -> None:
    api_url = _require_env("HA_API_URL")
    token = _require_env("HA_API_SECRET")
    entity_id = _require_env("HA_SATELLITE_ENTITY_ID")

    status, payload = _ha_get_json(
        base_url=normalize_rest_api_url(api_url),
        token=token,
        endpoint=f"/api/states/{entity_id}",
    )

    assert 200 <= status < 300, f"Expected HTTP success from /api/states/{entity_id}, got status={status}"
    assert isinstance(payload, dict), (
        f"Expected /api/states/{entity_id} payload to be an object, got {type(payload).__name__}"
    )
    assert payload.get("entity_id") == entity_id, (
        "Expected Home Assistant state payload entity_id to match HA_SATELLITE_ENTITY_ID"
    )
    assert "state" in payload, "Expected Home Assistant state payload to include a 'state' field"
