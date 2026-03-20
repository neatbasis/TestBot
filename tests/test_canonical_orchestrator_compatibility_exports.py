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
    assert "Prefer importing from testbot.canonical_turn_orchestrator" in compatibility_metadata["deprecation_note"]
