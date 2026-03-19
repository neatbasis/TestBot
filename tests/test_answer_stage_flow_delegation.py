from __future__ import annotations

import pytest

from testbot.pipeline_state import PipelineState
import testbot.sat_chatbot_memory_v2 as runtime


def _state() -> PipelineState:
    return PipelineState(user_input="hello")


def test_run_answer_stage_flow_deprecated_alias_surfaces_canonical_bypass_retirement() -> None:
    expected = _state()
    observed: dict[str, object] = {}

    def _fake_runner(*_args, **kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(runtime, "run_canonical_answer_stage_flow", _fake_runner)
    try:
        with pytest.warns(
            DeprecationWarning,
            match=r"run_answer_stage_flow.*run_canonical_answer_stage_flow.*2026-04-01",
        ):
            actual = runtime.run_answer_stage_flow(
                llm=object(),
                state=_state(),
                chat_history=[],
                hits=[],
                capability_status="ask_unavailable",
            )
    finally:
        monkeypatch.undo()
    assert actual is expected
    assert observed == {
        "chat_history": [],
        "hits": [],
        "capability_status": "ask_unavailable",
        "selected_decision": None,
        "runtime_capability_status": None,
        "clock": None,
        "timezone": "Europe/Helsinki",
    }


def test_canonical_answer_stage_flow_is_retired_to_prevent_raw_utterance_bypass() -> None:
    observed: dict[str, object] = {}

    def _fake_pipeline(**kwargs):
        observed.update(kwargs)
        return _state(), []

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _fake_pipeline)
    try:
        runtime.run_canonical_answer_stage_flow(
            llm=object(),
            state=_state(),
            chat_history=[],
            hits=[],
            capability_status="ask_unavailable",
        )
    finally:
        monkeypatch.undo()

    assert observed["utterance"] == "hello"
    assert observed["io_channel"] == "cli"


def test_evaluate_alignment_decision_shim_warns_and_strictly_passthroughs_to_logic_owner() -> None:
    expected = {"final_alignment_decision": "allow", "dimensions": {}}
    observed: dict[str, object] = {}

    def _fake_logic_alignment(**kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(runtime, "_evaluate_alignment_decision", _fake_logic_alignment)
    try:
        with pytest.warns(
            DeprecationWarning,
            match=r"evaluate_alignment_decision.*logic\.alignment.*2026-04-01",
        ):
            actual = runtime.evaluate_alignment_decision(
                user_input="hello",
                draft_answer="draft",
                final_answer="final",
                confidence_decision={"context_confident": True},
                claims=["claim"],
                provenance_types=[],
                basis_statement="basis",
            )
    finally:
        monkeypatch.undo()

    assert actual is expected
    assert observed["user_input"] == "hello"
    assert observed["draft_answer"] == "draft"
    assert observed["final_answer"] == "final"
    assert observed["confidence_decision"] == {"context_confident": True}
    assert observed["claims"] == ["claim"]
    assert observed["provenance_types"] == []
    assert observed["basis_statement"] == "basis"
    assert observed["is_clarification_answer"] is runtime.is_clarification_answer
    assert observed["is_capabilities_help_answer"] is runtime._is_capabilities_help_answer
    assert set(observed) == {
        "user_input",
        "draft_answer",
        "final_answer",
        "confidence_decision",
        "claims",
        "provenance_types",
        "basis_statement",
        "is_clarification_answer",
        "is_capabilities_help_answer",
    }


def test_no_parallel_full_turn_seeded_runner_symbol_exists() -> None:
    assert not hasattr(runtime, "_run_full_canonical_turn_from_seeded_artifacts")
