from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InteractionShape(str, Enum):
    CLI_TEXT_LOOP = "cli_text_loop"
    SATELLITE_VOICE_LOOP = "satellite_voice_loop"


@dataclass(frozen=True)
class NeedProfile:
    task_intent_requirements: str


@dataclass(frozen=True)
class ChannelContext:
    channel_id: str
    supports_satellite_ask: bool


@dataclass(frozen=True)
class InteractionStandardsProfile:
    profile_id: str
    deterministic_rationale: bool = False


@dataclass(frozen=True)
class InteractionPlanResult:
    recommended_shape: InteractionShape
    stable_id: str
    rationale: str | None = None


def plan_interaction(
    *,
    need_profile: NeedProfile,
    channel_context: ChannelContext,
    interaction_standards_profile: InteractionStandardsProfile,
) -> InteractionPlanResult:
    if channel_context.channel_id == "satellite" and channel_context.supports_satellite_ask:
        shape = InteractionShape.SATELLITE_VOICE_LOOP
    else:
        shape = InteractionShape.CLI_TEXT_LOOP

    stable_id = f"{interaction_standards_profile.profile_id}:{shape.value}"
    rationale = None
    if interaction_standards_profile.deterministic_rationale:
        rationale = (
            f"intent={need_profile.task_intent_requirements};"
            f"channel={channel_context.channel_id};"
            f"supports_satellite_ask={channel_context.supports_satellite_ask};"
            f"shape={shape.value}"
        )
    return InteractionPlanResult(recommended_shape=shape, stable_id=stable_id, rationale=rationale)
