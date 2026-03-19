from __future__ import annotations

import pytest

from testbot.pipeline_state import PipelineState
import testbot.sat_chatbot_memory_v2 as runtime


def _state() -> PipelineState:
    return PipelineState(user_input="hello")


def test_run_answer_stage_flow_deprecated_alias_surfaces_canonical_bypass_retirement() -> None:
    expected = _state()

    def _fake_runner(*_args, **_kwargs):
        return expected

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(runtime, "run_canonical_answer_stage_flow", _fake_runner)
    try:
        with pytest.warns(DeprecationWarning, match="run_answer_stage_flow"):
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


def test_no_parallel_full_turn_seeded_runner_symbol_exists() -> None:
    assert not hasattr(runtime, "_run_full_canonical_turn_from_seeded_artifacts")
