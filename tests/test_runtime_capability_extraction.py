from __future__ import annotations

from types import SimpleNamespace

from testbot import sat_chatbot_memory_v2 as runtime
from testbot.runtime_capability_service import (
    CapabilitySnapshotData,
    RuntimeCapabilityStatusData,
    build_runtime_capability_status,
)


def test_build_capability_snapshot_delegates_to_runtime_capability_service(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_service(**kwargs):
        captured.update(kwargs)
        return CapabilitySnapshotData(
            runtime=kwargs["runtime"],
            requested_mode="auto",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason="satellite connection is unavailable",
            exit_reason=None,
            ha_error="Missing HA_API_TOKEN",
            ollama_error=None,
            runtime_capability_status=RuntimeCapabilityStatusData(
                ollama_available=True,
                ha_available=False,
                effective_mode="cli",
                requested_mode="auto",
                daemon_mode=False,
                fallback_reason="satellite connection is unavailable",
                memory_backend="in_memory",
                debug_enabled=False,
                debug_verbose=False,
                text_clarification_available=True,
                satellite_ask_available=False,
            ),
        )

    monkeypatch.setattr(runtime, "build_capability_snapshot_from_service", _fake_service)

    snapshot = runtime.build_capability_snapshot(
        requested_mode="auto",
        daemon_mode=False,
        runtime={
            "ha_base_url": "http://localhost:8123",
            "ha_api_token": "token",
            "ha_satellite_entity_id": "assist_satellite.kitchen",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3.1:latest",
            "ollama_embedding_model": "nomic-embed-text",
        },
    )

    assert captured["requested_mode"] == "auto"
    assert captured["ha_connection_error_fn"] is runtime._ha_connection_error
    assert captured["ollama_connection_error_fn"] is runtime._ollama_connection_error
    assert snapshot.effective_mode == "cli"
    assert snapshot.runtime_capability_status.satellite_ask_available is False


def test_print_startup_status_delegates_to_presenter(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_presenter(*, snapshot):
        captured["snapshot"] = snapshot

    monkeypatch.setattr(runtime, "print_startup_status_from_presenter", _fake_presenter)
    snapshot = SimpleNamespace()

    runtime.print_startup_status(snapshot=snapshot)

    assert captured["snapshot"] is snapshot


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
