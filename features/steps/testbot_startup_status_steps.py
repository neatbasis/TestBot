from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

from testbot.sat_chatbot_memory_v2 import CapabilitySnapshot, RuntimeCapabilityStatus, _print_startup_status


def _make_snapshot(*, requested_mode: str, daemon_mode: bool, ha_error: str | None, ollama_error: str | None) -> CapabilitySnapshot:
    effective_mode = "satellite" if ha_error is None else "cli"
    fallback_reason = None if ha_error is None else "satellite connection is unavailable"
    runtime = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text",
        "ha_api_url": "http://localhost:8123",
        "ha_api_secret": "secret",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "memory_store_backend": "in_memory",
    }
    return CapabilitySnapshot(
        runtime=runtime,
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        effective_mode=effective_mode,
        fallback_reason=fallback_reason,
        exit_reason=None,
        ha_error=ha_error,
        ollama_error=ollama_error,
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=ollama_error is None,
            ha_available=ha_error is None,
            effective_mode=effective_mode,
            requested_mode=requested_mode,
            daemon_mode=daemon_mode,
            fallback_reason=fallback_reason,
            memory_backend="in_memory",
            debug_enabled=False,
            debug_verbose=False,
            text_clarification_available=True,
            satellite_ask_available=ha_error is None,
        ),
    )


from behave import given, then, when


@given('startup mode "{mode}" with daemon set to "{daemon}"')
def step_given_startup_mode(context, mode: str, daemon: str) -> None:
    context.startup_requested_mode = mode
    context.startup_daemon_mode = daemon.lower() == "true"


@given("Home Assistant connection is unavailable during startup checks")
def step_given_ha_unavailable(context) -> None:
    context.startup_ha_error = "Missing HA_API_SECRET"


@given("Ollama connection is available during startup checks")
def step_given_ollama_available(context) -> None:
    context.startup_ollama_error = None


@when("startup status is rendered")
def step_when_startup_rendered(context) -> None:
    snapshot = _make_snapshot(
        requested_mode=context.startup_requested_mode,
        daemon_mode=context.startup_daemon_mode,
        ha_error=context.startup_ha_error,
        ollama_error=context.startup_ollama_error,
    )
    stream = StringIO()
    with redirect_stdout(stream):
        _print_startup_status(snapshot=snapshot)
    context.startup_output = stream.getvalue()


@then('startup output should include "{expected}"')
def step_then_startup_output_includes(context, expected: str) -> None:
    assert expected in context.startup_output
