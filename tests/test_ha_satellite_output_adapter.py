from __future__ import annotations

from testbot.adapters.ha_satellite_output import send_satellite_output


def test_send_satellite_output_calls_assist_satellite_start_conversation() -> None:
    captured: dict[str, object] = {}

    class _FakeClient:
        def trigger_service(self, domain: str, service: str, **kwargs: object) -> None:
            captured["domain"] = domain
            captured["service"] = service
            captured["kwargs"] = kwargs

    send_satellite_output(_FakeClient(), "assist_satellite.office", "hello world")

    assert captured == {
        "domain": "assist_satellite",
        "service": "start_conversation",
        "kwargs": {
            "entity_id": "assist_satellite.office",
            "start_message": "hello world",
            "preannounce": False,
        },
    }
