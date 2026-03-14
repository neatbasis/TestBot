from __future__ import annotations

import os

import pytest

from tests.conftest import require_live_smoke_config
from homeassistant_api import Client
from homeassistant_api.errors import HomeassistantAPIError

from ha_ask.config import normalize_rest_api_url

pytestmark = pytest.mark.live_smoke

require_live_smoke_config(
    suite_name="live_smoke Home Assistant integration tests",
    required_fields=("HA_API_URL", "HA_API_SECRET", "HA_SATELLITE_ENTITY_ID"),
)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"Set {name} to run live_smoke Home Assistant integration tests")
    return value


def _ha_client() -> Client:
    api_url = _require_env("HA_API_URL")
    token = _require_env("HA_API_SECRET")
    return Client(normalize_rest_api_url(api_url), token)


def test_live_smoke_home_assistant_api_root_returns_message() -> None:
    _require_env("HA_SATELLITE_ENTITY_ID")
    client = _ha_client()

    assert client.check_api_running(), "Expected Home Assistant API root to report 'API running.'"


def test_live_smoke_home_assistant_states_contains_configured_satellite_entity() -> None:
    entity_id = _require_env("HA_SATELLITE_ENTITY_ID")
    client = _ha_client()

    try:
        state = client.get_state(entity_id=entity_id)
    except HomeassistantAPIError as exc:
        pytest.fail(
            f"Unable to fetch state for configured HA_SATELLITE_ENTITY_ID={entity_id!r}: {exc}. "
            "Verify HA_API_URL, HA_API_SECRET permissions, and entity id configuration."
        )

    assert state.entity_id == entity_id, (
        "Expected Home Assistant state payload entity_id to match HA_SATELLITE_ENTITY_ID"
    )
    assert isinstance(state.state, str), "Expected Home Assistant state payload to include a string 'state'"


def test_live_smoke_home_assistant_satellite_entity_is_actionable() -> None:
    entity_id = _require_env("HA_SATELLITE_ENTITY_ID")
    client = _ha_client()

    state = client.get_state(entity_id=entity_id)
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
