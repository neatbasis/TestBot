from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InteractionRequirements:
    """Transport-agnostic interaction requirements for user input collection flows."""

    stable_id_required: bool = True
    deterministic_field_collection_required: bool = True
    open_text_preferred: bool = True
    sentence_style_fit: str = "plain_sentence"
    machine_actionable: bool = True


__all__ = ["InteractionRequirements"]
