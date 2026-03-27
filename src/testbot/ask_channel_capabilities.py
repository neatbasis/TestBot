from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from testbot.interaction_standards import InteractionRequirements

AskChannel = Literal["terminal", "satellite", "mobile", "discord"]


@dataclass(frozen=True, slots=True)
class AskChannelCapabilities:
    """Explicit capability contract exposed by Ask channel adapters."""

    supports_freeform: bool
    supports_multichoice: bool
    supports_required_slots: bool
    supports_template_slot_extraction: bool
    supports_async_reply: bool
    supports_cancel: bool
    supports_explainer: bool


CHANNEL_CAPABILITIES: dict[AskChannel, AskChannelCapabilities] = {
    "terminal": AskChannelCapabilities(
        supports_freeform=True,
        supports_multichoice=True,
        supports_required_slots=True,
        supports_template_slot_extraction=False,
        supports_async_reply=False,
        supports_cancel=True,
        supports_explainer=True,
    ),
    "satellite": AskChannelCapabilities(
        supports_freeform=True,
        supports_multichoice=True,
        supports_required_slots=True,
        supports_template_slot_extraction=True,
        supports_async_reply=False,
        supports_cancel=True,
        supports_explainer=True,
    ),
    "mobile": AskChannelCapabilities(
        supports_freeform=True,
        supports_multichoice=True,
        supports_required_slots=True,
        supports_template_slot_extraction=False,
        supports_async_reply=True,
        supports_cancel=True,
        supports_explainer=True,
    ),
    "discord": AskChannelCapabilities(
        supports_freeform=True,
        supports_multichoice=True,
        supports_required_slots=True,
        supports_template_slot_extraction=False,
        supports_async_reply=True,
        supports_cancel=True,
        supports_explainer=True,
    ),
}


def capability_for_channel(channel: AskChannel) -> AskChannelCapabilities:
    return CHANNEL_CAPABILITIES[channel]


def validate_channel_interaction_requirements(
    *, channel: AskChannel, interaction_requirements: InteractionRequirements
) -> None:
    """Validate that requested interaction semantics fit channel capability."""

    interaction_requirements.validate()
    capabilities = capability_for_channel(channel)

    if interaction_requirements.stable_id_required and not capabilities.supports_multichoice:
        raise ValueError(
            f"Channel '{channel}' does not support stable-id multichoice interaction"
        )

    if (
        interaction_requirements.deterministic_field_collection_required
        and not capabilities.supports_required_slots
    ):
        raise ValueError(f"Channel '{channel}' does not support deterministic required-slot collection")

    if interaction_requirements.open_text_preferred and not capabilities.supports_freeform:
        raise ValueError(f"Channel '{channel}' does not support freeform interaction")


__all__ = [
    "AskChannel",
    "AskChannelCapabilities",
    "CHANNEL_CAPABILITIES",
    "capability_for_channel",
    "validate_channel_interaction_requirements",
]
