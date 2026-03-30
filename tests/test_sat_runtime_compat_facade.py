from __future__ import annotations

import pytest

from testbot import sat_chatbot_memory_v2 as runtime


def test_build_source_connector_wrapper_delegates_to_startup_owner(monkeypatch) -> None:
    runtime_payload = {"source_ingest_enabled": True, "source_connector_type": "fixture"}
    observed: dict[str, object] = {}
    expected = object()

    def _fake_build_source_connector(*, runtime, append_session_log):
        observed["runtime"] = runtime
        observed["append_session_log"] = append_session_log
        return expected

    monkeypatch.setattr(runtime, "build_startup_source_connector", _fake_build_source_connector)

    actual = runtime._build_source_connector(runtime_payload)

    assert actual is expected
    assert observed["runtime"] is runtime_payload
    assert observed["append_session_log"] is runtime.append_session_log


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


def test_turn_policy_logic_wrappers_delegate_to_canonical_logic_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime, "coerce_optional_string", lambda value: f"canonical:{value}")
    monkeypatch.setattr(runtime, "compute_turn_policy_ambiguity_score", lambda confidence_decision: 0.1234)

    assert runtime._optional_string("x") == "canonical:x"
    assert runtime._ambiguity_score({"scored_candidates": []}) == 0.1234
