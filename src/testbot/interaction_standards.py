from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InteractionRequirements:
    """Transport-agnostic contract for user-input collection behavior.

    Field semantics:
    - stable_id_required: choices should carry stable machine ids when offered.
    - deterministic_field_collection_required: runtime should avoid nondeterministic
      collection settings (for example, fractional timeout jitter).
    - open_text_preferred: prompts should favor free-form response language.
    - sentence_style_fit: prompt sentence framing style contract ("plain_sentence"
      or "structured_sentence").
    - machine_actionable: responses should include actionable command language.
    """

    stable_id_required: bool = True
    deterministic_field_collection_required: bool = True
    open_text_preferred: bool = True
    sentence_style_fit: str = "plain_sentence"
    machine_actionable: bool = True

    def validate(self) -> None:
        if self.sentence_style_fit not in {"plain_sentence", "structured_sentence"}:
            raise ValueError(f"Unsupported sentence_style_fit: {self.sentence_style_fit}")
        if self.deterministic_field_collection_required and not self.stable_id_required:
            raise ValueError(
                "deterministic_field_collection_required requires stable_id_required"
            )


__all__ = ["InteractionRequirements"]
