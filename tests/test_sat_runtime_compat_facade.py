from __future__ import annotations

from testbot import sat_chatbot_memory_v2 as runtime


def test_compatibility_reexport_manifest_remains_governed() -> None:
    manifest = runtime._COMPATIBILITY_REEXPORTS
    assert "CanonicalTurnOrchestrator" in manifest
    assert manifest["CanonicalTurnOrchestrator"]["owner_decision"] == "compatibility_only"


def test_compatibility_exports_include_governed_retirement_metadata() -> None:
    metadata = runtime._COMPATIBILITY_REEXPORTS["CanonicalTurnOrchestrator"]

    assert metadata["status"] == "compatibility re-export"
    assert metadata["owner_decision"] == "compatibility_only"
    assert metadata["removal_criteria"]
    assert metadata["deprecation_note"]


def test_bucket_c_symbols_are_not_public_compatibility_exports() -> None:
    bucket_c_removed_exports = {
        "AnswerValidateResult",
        "ambiguity_score",
        "intent_label",
        "derive_response_blocker_reason",
        "user_followup_signal_proxy",
    }

    assert bucket_c_removed_exports.isdisjoint(set(runtime.__all__))


def test_compatibility_manifest_symbols_remain_public_exports() -> None:
    exported = set(runtime.__all__)
    for symbol in runtime._COMPATIBILITY_REEXPORTS:
        assert symbol in exported
