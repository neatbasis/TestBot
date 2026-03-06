from __future__ import annotations

import os

import pytest
from homeassistant_api import Client
from homeassistant_api.errors import HomeassistantAPIError

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

    try:
        state = client.get_state(entity_id=entity_id)
    except HomeassistantAPIError as exc:
        pytest.fail(
            f"Configured HA_SATELLITE_ENTITY_ID={entity_id!r} is missing or inaccessible: {exc}. "
            "Check the configured entity id and Home Assistant token permissions."
        )

    attributes = state.attributes
    assert isinstance(attributes, dict), (
        f"Configured HA_SATELLITE_ENTITY_ID={entity_id!r} returned missing/invalid attributes payload."
    )

    attr_keys = {str(key).lower() for key in attributes}
    expected_attribute_hints = {"assist", "pipeline", "mic", "wake", "satellite", "stt", "tts"}
    assert any(any(hint in key for hint in expected_attribute_hints) for key in attr_keys), (
        "Configured HA_SATELLITE_ENTITY_ID entity did not expose any expected assist/satellite attributes. "
        f"entity_id={entity_id!r}, attribute_keys={sorted(attr_keys)!r}"
    )

    homeassistant_domain = client.get_domain("homeassistant")
    if homeassistant_domain and "update_entity" in homeassistant_domain.services:
        try:
            changed_states = client.trigger_service("homeassistant", "update_entity", entity_id=entity_id)
        except HomeassistantAPIError as exc:
            pytest.fail(
                "Expected Home Assistant update_entity to succeed for configured "
                f"HA_SATELLITE_ENTITY_ID={entity_id!r}, but request failed: {exc}"
            )
        assert isinstance(changed_states, tuple), (
            "Expected Home Assistant update_entity response to be a tuple of state changes "
            f"for HA_SATELLITE_ENTITY_ID={entity_id!r}, got {type(changed_states).__name__}"
        )
