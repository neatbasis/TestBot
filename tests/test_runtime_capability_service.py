from __future__ import annotations

from testbot.application.services.runtime_capability_service import (
    build_capability_snapshot,
    resolve_effective_mode,
)


def _runtime() -> dict[str, object]:
    return {
        "ha_api_url": "http://localhost:8123",
        "ha_api_token": "token",
        "ha_satellite_entity_id": "assist_satellite.kitchen",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.1:latest",
        "ollama_embedding_model": "nomic-embed-text:latest",
        "x_ollama_key": "",
        "memory_store_backend": "in_memory",
        "debug_verbose": False,
    }


def test_resolve_effective_mode_auto_with_ha_available() -> None:
    mode, fallback_reason, exit_reason = resolve_effective_mode(
        requested_mode="auto",
        daemon_mode=False,
        ha_error=None,
        ollama_error=None,
    )
    assert mode == "satellite"
    assert fallback_reason is None
    assert exit_reason is None


def test_resolve_effective_mode_auto_with_ha_unavailable_cli_fallback() -> None:
    mode, fallback_reason, exit_reason = resolve_effective_mode(
        requested_mode="auto",
        daemon_mode=False,
        ha_error="Missing HA_API_TOKEN",
        ollama_error=None,
    )
    assert mode == "cli"
    assert fallback_reason == "satellite connection is unavailable"
    assert exit_reason is None


def test_resolve_effective_mode_daemon_with_ha_unavailable_exits() -> None:
    mode, fallback_reason, exit_reason = resolve_effective_mode(
        requested_mode="auto",
        daemon_mode=True,
        ha_error="auth failed",
        ollama_error=None,
    )
    assert mode is None
    assert fallback_reason is None
    assert exit_reason == "Home Assistant is unavailable: auth failed"


def test_build_capability_snapshot_marks_ollama_unavailable(monkeypatch) -> None:
    from testbot.application.services import runtime_capability_service as service

    monkeypatch.setattr(service, "ha_connection_error", lambda *_args: None)
    monkeypatch.setattr(service, "ollama_connection_error", lambda *_args, **_kwargs: "missing models")

    snapshot = build_capability_snapshot(requested_mode="auto", daemon_mode=False, runtime=_runtime())

    assert snapshot.effective_mode is None
    assert snapshot.exit_reason == "Ollama is unavailable: missing models"
    assert snapshot.runtime_capability_status.ollama_available is False
