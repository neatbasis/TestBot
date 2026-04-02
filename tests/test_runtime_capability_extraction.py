from __future__ import annotations

from testbot.runtime_capability_service import (
    build_runtime_capability_status,
)


def test_build_runtime_capability_status_reports_actual_channel_resolution() -> None:
    status = build_runtime_capability_status(
        requested_mode="satellite",
        effective_mode="satellite",
        daemon_mode=False,
        fallback_reason=None,
        runtime={"memory_store_backend": "in_memory", "debug_verbose": False},
        ha_error="Missing HA_API_TOKEN",
        ollama_error=None,
    )

    assert status.resolved_channel == "terminal"
    assert status.resolution_source == "named_fallback"
    assert status.fallback_used is True
    assert status.resolution_fallback_reason == "policy_override_recent_unavailable"
    assert status.satellite_ask_available is False
    assert status.ask_runtime_state == "terminal_only"
    assert status.available_ask_channels == ("terminal",)
    assert status.primary_ask_channel == "terminal"


def test_build_runtime_capability_status_reports_ask_runtime_available_in_cli_mode() -> None:
    status = build_runtime_capability_status(
        requested_mode="cli",
        effective_mode="cli",
        daemon_mode=False,
        fallback_reason=None,
        runtime={"memory_store_backend": "in_memory", "debug_verbose": False},
        ha_error="Missing HA_API_TOKEN",
        ollama_error=None,
    )

    assert status.text_clarification_available is True
    assert status.satellite_ask_available is False
    assert status.resolved_channel == "terminal"
    assert status.ask_runtime_state == "terminal_only"


def test_build_runtime_capability_status_reports_ask_runtime_available_in_satellite_mode() -> None:
    status = build_runtime_capability_status(
        requested_mode="satellite",
        effective_mode="satellite",
        daemon_mode=False,
        fallback_reason=None,
        runtime={"memory_store_backend": "in_memory", "debug_verbose": False},
        ha_error=None,
        ollama_error=None,
    )

    assert status.text_clarification_available is True
    assert status.satellite_ask_available is True
    assert status.ask_runtime_state == "multi_channel"
    assert status.available_ask_channels == ("terminal", "satellite")
    assert status.resolved_channel == "satellite"


def test_build_runtime_capability_status_reports_satellite_only_channel_in_daemon_satellite_mode() -> None:
    status = build_runtime_capability_status(
        requested_mode="satellite",
        effective_mode="satellite",
        daemon_mode=True,
        fallback_reason=None,
        runtime={"memory_store_backend": "in_memory", "debug_verbose": False},
        ha_error=None,
        ollama_error=None,
    )

    assert status.ask_runtime_state == "satellite_available"
    assert status.available_ask_channels == ("satellite",)
    assert status.primary_ask_channel == "satellite"
    assert status.ask_runtime_reason is None


def test_build_runtime_capability_status_reports_misconfigured_when_daemon_has_no_ask_channel() -> None:
    status = build_runtime_capability_status(
        requested_mode="satellite",
        effective_mode=None,
        daemon_mode=True,
        fallback_reason=None,
        runtime={"memory_store_backend": "in_memory", "debug_verbose": False},
        ha_error="Missing HA_API_TOKEN",
        ollama_error=None,
    )

    assert status.text_clarification_available is False
    assert status.satellite_ask_available is False
    assert status.ask_runtime_state == "misconfigured"
    assert status.available_ask_channels == ()
    assert status.primary_ask_channel is None
    assert status.ask_runtime_reason == "daemon_requested_without_usable_ask_channel"
    assert status.resolved_channel is None
