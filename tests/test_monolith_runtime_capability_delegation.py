from __future__ import annotations

from testbot import sat_chatbot_memory_v2 as runtime


def test_monolith_capability_probe_delegates_to_runtime_service_aliases(monkeypatch) -> None:
    calls = {"ha": 0, "ollama": 0, "status": 0}

    monkeypatch.setattr(runtime, "_ha_connection_error_service", lambda *_args, **_kwargs: (calls.__setitem__("ha", calls["ha"] + 1) or "Missing HA_API_TOKEN"))
    monkeypatch.setattr(runtime, "_ollama_connection_error_service", lambda *_args, **_kwargs: (calls.__setitem__("ollama", calls["ollama"] + 1) or None))

    def _fake_status(*, requested_mode, effective_mode, daemon_mode, fallback_reason, runtime, ha_error, ollama_error):
        calls["status"] += 1
        return runtime_module.RuntimeCapabilityStatus(
            ollama_available=ollama_error is None,
            ha_available=ha_error is None,
            effective_mode=effective_mode or "unavailable",
            requested_mode=requested_mode,
            daemon_mode=daemon_mode,
            fallback_reason=fallback_reason,
            memory_backend=str(runtime.get("memory_store_backend", "unknown")),
            debug_enabled=False,
            debug_verbose=False,
            text_clarification_available=True,
            satellite_ask_available=False,
        )

    from testbot.application.services import runtime_capability_service as runtime_module

    monkeypatch.setattr(runtime, "_build_runtime_capability_status", _fake_status)

    snapshot = runtime.build_capability_snapshot(
        requested_mode="auto",
        daemon_mode=False,
        runtime={
            "ha_api_url": "http://localhost:8123",
            "ha_api_token": "",
            "ha_satellite_entity_id": "assist_satellite.kitchen",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3.1:latest",
            "ollama_embedding_model": "nomic-embed-text:latest",
            "x_ollama_key": "",
            "memory_store_backend": "in_memory",
            "debug_verbose": False,
        },
    )

    assert calls == {"ha": 1, "ollama": 1, "status": 1}
    assert snapshot.effective_mode == "cli"


def test_monolith_startup_status_printing_delegates_presenter(monkeypatch) -> None:
    captured = {"called": False}

    def _fake_presenter(*, snapshot):
        captured["called"] = True
        assert snapshot.requested_mode == "auto"

    monkeypatch.setattr(runtime, "_print_startup_status_service", _fake_presenter)

    runtime.print_startup_status(
        snapshot=runtime.CapabilitySnapshot(
            runtime={
                "ollama_base_url": "http://localhost:11434",
                "ollama_model": "llama3.1:latest",
                "ollama_embedding_model": "nomic-embed-text:latest",
                "ha_api_url": "http://localhost:8123",
                "ha_satellite_entity_id": "assist_satellite.kitchen",
                "memory_store_backend": "in_memory",
            },
            requested_mode="auto",
            daemon_mode=False,
            effective_mode="cli",
            fallback_reason="satellite connection is unavailable",
            exit_reason=None,
            ha_error="Missing HA_API_TOKEN",
            ollama_error=None,
            runtime_capability_status=runtime.RuntimeCapabilityStatus(
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
    )

    assert captured["called"] is True
