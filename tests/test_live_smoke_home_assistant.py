from __future__ import annotations

import os
import time

import pytest

from tests.live_smoke_support import require_live_smoke_config
from homeassistant_api import Client
from homeassistant_api.errors import HomeassistantAPIError, InternalServerError

from ask.config import normalize_rest_api_url

pytestmark = pytest.mark.live_smoke

require_live_smoke_config(
    suite_name="live_smoke Home Assistant integration tests",
    required_fields=("HA_BASE_URL", "HA_API_TOKEN", "HA_SATELLITE_ENTITY_ID"),
)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run live_smoke Home Assistant integration tests")
    return value


def _ha_client() -> Client:
    api_url = _require_env("HA_BASE_URL")
    token = _require_env("HA_API_TOKEN")
    return Client(normalize_rest_api_url(api_url), token)


def _retry_transient_ha_server_errors(fn, *, attempts: int = 3, delay_s: float = 0.3):
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except InternalServerError as exc:
            last_exc = exc
            if attempt >= attempts:
                raise
            time.sleep(delay_s)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Unreachable retry state in _retry_transient_ha_server_errors")


def test_live_smoke_home_assistant_api_root_returns_message() -> None:
    _require_env("HA_SATELLITE_ENTITY_ID")
    client = _ha_client()

    assert _retry_transient_ha_server_errors(client.check_api_running), (
        "Expected Home Assistant API root to report 'API running.'"
    )


def test_live_smoke_home_assistant_states_contains_configured_satellite_entity() -> None:
    entity_id = _require_env("HA_SATELLITE_ENTITY_ID")
    client = _ha_client()

    try:
        state = _retry_transient_ha_server_errors(lambda: client.get_state(entity_id=entity_id))
    except HomeassistantAPIError as exc:
        pytest.fail(
            f"Unable to fetch state for configured HA_SATELLITE_ENTITY_ID={entity_id!r}: {exc}. "
            "Verify HA_BASE_URL, HA_API_TOKEN permissions, and entity id configuration."
        )

    assert state.entity_id == entity_id, (
        "Expected Home Assistant state payload entity_id to match HA_SATELLITE_ENTITY_ID"
    )
    assert isinstance(state.state, str), "Expected Home Assistant state payload to include a string 'state'"


def test_live_smoke_home_assistant_satellite_entity_is_actionable() -> None:
    entity_id = _require_env("HA_SATELLITE_ENTITY_ID")
    client = _ha_client()

    state = _retry_transient_ha_server_errors(lambda: client.get_state(entity_id=entity_id))
    attributes = state.attributes

    assert entity_id.startswith("assist_satellite."), (
        f"Configured HA_SATELLITE_ENTITY_ID must be an assist_satellite entity, got {entity_id!r}"
    )
    assert isinstance(attributes, dict), (
        f"Configured HA_SATELLITE_ENTITY_ID={entity_id!r} returned missing/invalid attributes payload."
    )
    assert isinstance(attributes.get("supported_features"), int), (
        "Configured HA_SATELLITE_ENTITY_ID entity did not expose an integer supported_features value. "
        f"entity_id={entity_id!r}, attribute_keys={sorted(str(k).lower() for k in attributes)!r}"
    )
