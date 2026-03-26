from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ask import Answer, AskClient, AskSpec
from ask.config import Config
from ask.config import normalize_rest_api_url


STOP_DECISION_ID = "stop_satellite_loop"


@dataclass(frozen=True)
class AskTurnInput:
    decision_id: str | None
    sentence: str
    error: str | None


class AskGateway:
    """TestBot-owned Ask seam.

    TestBot decides *why* it needs interaction and how to interpret stable ids.
    Ask executes channel-aware prompting/collection.
    """

    def __init__(self, client: AskClient) -> None:
        self._client = client

    @classmethod
    def from_home_assistant(
        cls,
        *,
        ha_api_url: str,
        ha_api_token: str,
        satellite_entity_id: str,
        notify_action: str | None = None,
        discord_turn_service_url: str | None = None,
    ) -> "AskGateway":
        cfg = Config(
            ha_api_url=ha_api_url,
            ha_api_token=ha_api_token,
            satellite_entity_id=satellite_entity_id,
            notify_action=notify_action,
            discord_turn_service_url=discord_turn_service_url,
        )
        return cls(AskClient(cfg))

    @classmethod
    def from_runtime(cls, runtime: Mapping[str, object]) -> "AskGateway":
        return cls.from_home_assistant(
            ha_api_url=str(runtime["ha_api_url"]),
            ha_api_token=str(runtime["ha_api_token"]),
            satellite_entity_id=str(runtime["ha_satellite_entity_id"]),
            notify_action=str(runtime.get("ha_notify_action") or "") or None,
            discord_turn_service_url=str(runtime.get("discord_turn_service_url") or "") or None,
        )

    @property
    def ha_api_token(self) -> str:
        return str(self._client.config.ha_api_token or "")

    @property
    def satellite_entity_id(self) -> str:
        return str(self._client.config.satellite_entity_id or "")

    def normalized_ha_rest_url(self) -> str:
        return normalize_rest_api_url(str(self._client.config.ha_api_url or ""))

    def request_satellite_turn_input(self, *, question: str, timeout_s: float = 60.0) -> AskTurnInput:
        spec = AskSpec(
            question=question,
            answers=(
                Answer(id=STOP_DECISION_ID, sentences=("stop", "exit", "quit"), title="Stop"),
            ),
            timeout_s=timeout_s,
        )
        result = self._client.ask_question(channel="satellite", spec=spec)
        return AskTurnInput(
            decision_id=_optional_str(result.get("id")),
            sentence=_optional_str(result.get("sentence")) or "",
            error=_optional_str(result.get("error")),
        )


def _optional_str(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["AskGateway", "AskTurnInput", "STOP_DECISION_ID"]
