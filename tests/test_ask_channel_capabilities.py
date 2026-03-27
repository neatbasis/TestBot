from __future__ import annotations

import pytest

from testbot.ask_channel_capabilities import capability_for_channel, validate_channel_interaction_requirements
from testbot.interaction_standards import InteractionRequirements


def test_terminal_channel_capabilities_support_structured_and_freeform_contract() -> None:
    terminal = capability_for_channel("terminal")

    assert terminal.supports_freeform is True
    assert terminal.supports_multichoice is True
    assert terminal.supports_required_slots is True
    assert terminal.supports_cancel is True


def test_validate_channel_interaction_requirements_accepts_terminal_defaults() -> None:
    validate_channel_interaction_requirements(
        channel="terminal",
        interaction_requirements=InteractionRequirements(),
    )


def test_validate_channel_interaction_requirements_rejects_interaction_contract_mismatch() -> None:
    with pytest.raises(ValueError, match="requires stable_id_required"):
        validate_channel_interaction_requirements(
            channel="terminal",
            interaction_requirements=InteractionRequirements(
                stable_id_required=False,
                deterministic_field_collection_required=True,
            ),
        )
