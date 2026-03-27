from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ask import Answer, AskClient, AskSpec
from ask.config import Config
from ask.config import normalize_rest_api_url

from testbot.interaction_standards import InteractionRequirements


STOP_DECISION_ID = "stop_satellite_loop"


def normalize_ha_rest_url(api_url: str) -> str:
    """Normalize a Home Assistant base URL to the canonical REST API endpoint."""
    return normalize_rest_api_url(api_url)


@dataclass(frozen=True)
class AskTurnInput:
    decision_id: str | None
    sentence: str
    error: str | None


class AskGateway:
    """TestBot-owned Ask seam.

    TestBot decides *why* it needs interaction and how to interpret stable ids.
    AskGateway does not select interaction profiles; it translates supplied requirements to AskSpec.
    Ask executes channel-aware prompting/collection.
    """

    def __init__(self, client: AskClient) -> None:
        self._client = client

    @classmethod
    def from_home_assistant(
        cls,
        *,
        ha_base_url: str,
        ha_api_token: str,
        satellite_entity_id: str,
        notify_action: str | None = None,
        discord_turn_service_url: str | None = None,
    ) -> "AskGateway":
        cfg = Config(
            ha_api_url=ha_base_url,
            ha_api_token=ha_api_token,
            satellite_entity_id=satellite_entity_id,
            notify_action=notify_action,
            discord_turn_service_url=discord_turn_service_url,
        )
        return cls(AskClient(cfg))

    @classmethod
    def from_runtime(cls, runtime: Mapping[str, object]) -> "AskGateway":
        return cls.from_home_assistant(
            ha_base_url=str(runtime["ha_base_url"]),
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
        return normalize_ha_rest_url(str(self._client.config.ha_api_url or ""))

    def satellite_turn_spec(
        self,
        *,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskSpec:
        interaction_requirements.validate()
        formatted_question = _format_question(
            question=question,
            sentence_style_fit=interaction_requirements.sentence_style_fit,
            open_text_preferred=interaction_requirements.open_text_preferred,
        )
        answers = (
            (
                Answer(
                    id=STOP_DECISION_ID,
                    sentences=("stop", "exit", "quit"),
                    title="Stop" if interaction_requirements.machine_actionable else "Cancel",
                ),
            )
            if interaction_requirements.stable_id_required
            else None
        )
        effective_timeout_s = (
            float(int(timeout_s))
            if interaction_requirements.deterministic_field_collection_required
            else timeout_s
        )

        return AskSpec(
            question=formatted_question,
            answers=answers,
            timeout_s=effective_timeout_s,
        )

    def request_satellite_turn_input(
        self,
        *,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskTurnInput:
        spec = self.satellite_turn_spec(
            question=question,
            timeout_s=timeout_s,
            interaction_requirements=interaction_requirements,
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


def _format_question(*, question: str, sentence_style_fit: str, open_text_preferred: bool) -> str:
    base = question.strip()
    if sentence_style_fit == "structured_sentence":
        base = f"Respond with one clear sentence: {base}"
    if not base.endswith(("?", ".", "!")):
        base = f"{base}."
    if open_text_preferred:
        return base
    return f"{base} Prefer one of the listed actions when possible."


__all__ = ["AskGateway", "AskTurnInput", "STOP_DECISION_ID", "normalize_ha_rest_url"]
