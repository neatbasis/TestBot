from __future__ import annotations

from types import SimpleNamespace

from testbot import sat_chatbot_memory_v2 as runtime


def test_build_capability_snapshot_delegates_to_runtime_capability_service(monkeypatch) -> None:
    captured: dict[str, object] = {}
    sentinel = SimpleNamespace(name="snapshot")

    def _fake_service(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(runtime, "build_capability_snapshot_from_service", _fake_service)

    result = runtime.build_capability_snapshot(
        requested_mode="auto",
        daemon_mode=False,
        runtime={
            "ha_api_url": "http://localhost:8123",
            "ha_api_token": "token",
            "ha_satellite_entity_id": "assist_satellite.kitchen",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3.1:latest",
            "ollama_embedding_model": "nomic-embed-text",
        },
    )

    assert result is sentinel
    assert captured["requested_mode"] == "auto"
    assert captured["runtime_capability_status_factory"] is runtime.RuntimeCapabilityStatus
    assert captured["capability_snapshot_factory"] is runtime.CapabilitySnapshot
    assert captured["ha_connection_error_fn"] is runtime._ha_connection_error
    assert captured["ollama_connection_error_fn"] is runtime._ollama_connection_error


def test_print_startup_status_delegates_to_presenter(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_presenter(*, snapshot):
        captured["snapshot"] = snapshot

    monkeypatch.setattr(runtime, "print_startup_status_from_presenter", _fake_presenter)
    snapshot = SimpleNamespace()

    runtime.print_startup_status(snapshot=snapshot)

    assert captured["snapshot"] is snapshot
