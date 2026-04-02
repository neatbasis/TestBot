from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ask import Answer, AskClient, AskSpec
from ask.config import Config
from ask.config import normalize_rest_api_url

from testbot.ask_channel_capabilities import AskChannel, validate_channel_interaction_requirements
from testbot.interaction_policy import (
    COLLECT_TURN_INPUT_INTENT,
    ChannelContext,
    InteractionPolicyRequest,
    ResolutionSource,
    resolve_channel_context,
)
from testbot.interaction_standards import InteractionRequirements


STOP_DECISION_ID = "stop_satellite_loop"


def normalize_ha_rest_url(base_url: str) -> str:
    """Normalize a Home Assistant base URL to the canonical REST API endpoint."""
    return normalize_rest_api_url(base_url)


@dataclass(frozen=True)
class AskTurnInput:
    decision_id: str | None
    sentence: str
    error: str | None
    resolved_channel: AskChannel | None = None
    resolution_source: ResolutionSource | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None


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
            api_url=ha_base_url,
            token=ha_api_token,
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
        return normalize_ha_rest_url(str(self._client.config.api_url or ""))

    def turn_spec(
        self,
        *,
        channel: AskChannel,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskSpec:
        validate_channel_interaction_requirements(
            channel=channel,
            interaction_requirements=interaction_requirements,
        )
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

    def request_turn_input(
        self,
        *,
        channel: AskChannel,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskTurnInput:
        spec = self.turn_spec(
            channel=channel,
            question=question,
            timeout_s=timeout_s,
            interaction_requirements=interaction_requirements,
        )
        result = self._client.ask_question(channel=channel, spec=spec)
        return AskTurnInput(
            decision_id=_optional_str(result.get("id")),
            sentence=_optional_str(result.get("sentence")) or "",
            error=_optional_str(result.get("error")),
            resolved_channel=channel,
            resolution_source="explicit_policy_channel",
            fallback_used=False,
            fallback_reason=None,
        )

    def request_turn_input_for_policy(
        self,
        *,
        interaction_policy: InteractionPolicyRequest,
        question: str,
        timeout_s: float = 60.0,
        allowed_channel_contexts: frozenset[ChannelContext] | None = None,
        explicit_override_channel_context: ChannelContext | None = None,
        recent_successful_channel_context: ChannelContext | None = None,
    ) -> AskTurnInput:
        if interaction_policy.intent != COLLECT_TURN_INPUT_INTENT:
            raise ValueError(f"Unsupported interaction policy intent: {interaction_policy.intent}")
        channel_resolution = resolve_channel_context(
            interaction_policy=interaction_policy,
            allowed_channels=allowed_channel_contexts or frozenset({"satellite", "cli"}),
            explicit_override_channel_context=explicit_override_channel_context,
            recent_successful_channel_context=recent_successful_channel_context,
        )
        resolved_channel: AskChannel = (
            "satellite" if channel_resolution.resolved_channel_context == "satellite" else "terminal"
        )
        result = self.request_turn_input(
            channel=resolved_channel,
            question=question,
            timeout_s=timeout_s,
            interaction_requirements=interaction_policy.interaction_requirements,
        )
        return AskTurnInput(
            decision_id=result.decision_id,
            sentence=result.sentence,
            error=result.error,
            resolved_channel=resolved_channel,
            resolution_source=channel_resolution.resolution_source,
            fallback_used=channel_resolution.fallback_used,
            fallback_reason=channel_resolution.fallback_reason,
        )

    def satellite_turn_spec(
        self,
        *,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskSpec:
        return self.turn_spec(
            channel="satellite",
            question=question,
            timeout_s=timeout_s,
            interaction_requirements=interaction_requirements,
        )

    def request_satellite_turn_input(
        self,
        *,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskTurnInput:
        return self.request_turn_input(
            channel="satellite",
            question=question,
            timeout_s=timeout_s,
            interaction_requirements=interaction_requirements,
        )

    def request_terminal_turn_input(
        self,
        *,
        question: str,
        timeout_s: float = 60.0,
        interaction_requirements: InteractionRequirements,
    ) -> AskTurnInput:
        return self.request_turn_input(
            channel="terminal",
            question=question,
            timeout_s=timeout_s,
            interaction_requirements=interaction_requirements,
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
