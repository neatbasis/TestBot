from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from testbot.interaction_standards import InteractionRequirements


def test_interaction_requirements_defaults_match_expected_contract() -> None:
    profile = InteractionRequirements()

    assert profile.stable_id_required is True
    assert profile.deterministic_field_collection_required is True
    assert profile.open_text_preferred is True
    assert profile.sentence_style_fit == "plain_sentence"
    assert profile.machine_actionable is True


def test_interaction_requirements_support_explicit_profile_construction() -> None:
    profile = InteractionRequirements(
        stable_id_required=False,
        deterministic_field_collection_required=False,
        open_text_preferred=False,
        sentence_style_fit="structured_sentence",
        machine_actionable=False,
    )

    assert profile == InteractionRequirements(
        stable_id_required=False,
        deterministic_field_collection_required=False,
        open_text_preferred=False,
        sentence_style_fit="structured_sentence",
        machine_actionable=False,
    )


def test_interaction_requirements_are_immutable() -> None:
    profile = InteractionRequirements()

    with pytest.raises(FrozenInstanceError):
        profile.stable_id_required = False  # type: ignore[misc]


def test_interaction_requirements_reject_unknown_sentence_style_fit() -> None:
    profile = InteractionRequirements(sentence_style_fit="unknown")

    with pytest.raises(ValueError, match="Unsupported sentence_style_fit"):
        profile.validate()


def test_interaction_requirements_require_stable_ids_for_deterministic_collection() -> None:
    profile = InteractionRequirements(
        stable_id_required=False,
        deterministic_field_collection_required=True,
    )

    with pytest.raises(ValueError, match="requires stable_id_required"):
        profile.validate()
