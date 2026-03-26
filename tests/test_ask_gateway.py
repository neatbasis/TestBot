from __future__ import annotations

from ask import AskClient
from ask.config import Config

from testbot.adapters.ask_gateway import AskGateway, STOP_DECISION_ID


def test_ask_gateway_builds_client_from_runtime_mapping() -> None:
    gateway = AskGateway.from_runtime(
        {
            "ha_api_url": "http://localhost:8123",
            "ha_api_token": "secret-token",
            "ha_satellite_entity_id": "assist_satellite.kitchen",
            "ha_notify_action": "mobile_app_phone",
            "discord_turn_service_url": "http://discord-turn.internal",
        }
    )

    assert gateway.ha_api_token == "secret-token"
    assert gateway.satellite_entity_id == "assist_satellite.kitchen"
    assert gateway.normalized_ha_rest_url().endswith("/api/")


def test_ask_gateway_satellite_prompt_uses_stable_stop_decision_id() -> None:
    captured: dict[str, object] = {}

    class _FakeAskClient(AskClient):
        def __init__(self) -> None:
            super().__init__(
                Config(
                    ha_api_url="http://localhost:8123",
                    ha_api_token="secret",
                    satellite_entity_id="assist_satellite.kitchen",
                )
            )

        def ask_question(self, *, channel, spec, **_kwargs):  # type: ignore[override]
            captured["channel"] = channel
            captured["spec"] = spec
            return {"id": STOP_DECISION_ID, "sentence": None, "error": None}

    gateway = AskGateway(_FakeAskClient())
    result = gateway.request_satellite_turn_input(question="Ask one memory-grounded question.")

    assert captured["channel"] == "satellite"
    spec = captured["spec"]
    assert spec.answers is not None
    assert spec.answers[0].id == STOP_DECISION_ID
    assert result.decision_id == STOP_DECISION_ID
    assert result.sentence == ""
