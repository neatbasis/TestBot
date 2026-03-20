from __future__ import annotations

from testbot import canonical_turn_orchestrator as canonical_owner
from testbot import sat_chatbot_memory_v2 as compatibility_module


def test_canonical_turn_orchestrator_is_available_from_compatibility_module() -> None:
    assert hasattr(compatibility_module, "CanonicalTurnOrchestrator")


def test_canonical_turn_orchestrator_reexport_points_to_canonical_owner() -> None:
    assert compatibility_module.CanonicalTurnOrchestrator is canonical_owner.CanonicalTurnOrchestrator


def test_canonical_turn_orchestrator_compatibility_intent_is_documented() -> None:
    compatibility_metadata = compatibility_module._COMPATIBILITY_REEXPORTS["CanonicalTurnOrchestrator"]
    assert compatibility_metadata["status"] == "compatibility re-export"
    assert compatibility_metadata["canonical_symbol"] == "testbot.canonical_turn_orchestrator.CanonicalTurnOrchestrator"
    assert compatibility_metadata["owner_decision"] == "compatibility_only"
    assert compatibility_metadata["introduced_for_compatibility_on"] == "2026-03-20"
    assert compatibility_metadata["review_after"] == "2026-06-30"
    assert compatibility_metadata["removal_criteria"].startswith("remove after all in-repo imports")
    assert "Prefer importing from testbot.canonical_turn_orchestrator" in compatibility_metadata["deprecation_note"]


def test_canonical_turn_orchestrator_is_intentional_compatibility_export_contract() -> None:
    assert "CanonicalTurnOrchestrator" in compatibility_module.__all__
    assert compatibility_module.CanonicalTurnOrchestrator.__module__ == "testbot.canonical_turn_orchestrator"
