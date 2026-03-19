from __future__ import annotations

from collections import deque

import pytest

from testbot.pipeline_state import PipelineState
import testbot.sat_chatbot_memory_v2 as runtime


def _state() -> PipelineState:
    return PipelineState(user_input="hello")


def test_run_answer_stage_flow_delegates_to_canonical_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = _state()
    observed: dict[str, object] = {}

    def _fake_canonical_runner(*args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return expected

    monkeypatch.setattr(runtime, "run_canonical_answer_stage_flow", _fake_canonical_runner)

    with pytest.warns(DeprecationWarning, match="run_answer_stage_flow"):
        actual = runtime.run_answer_stage_flow(
            llm=object(),
            state=_state(),
            chat_history=deque(),
            hits=[],
            capability_status="ask_unavailable",
        )

    assert actual is expected
    assert isinstance(observed["kwargs"]["chat_history"], deque)
    assert not observed["kwargs"]["chat_history"]
    assert observed["kwargs"]["hits"] == []


def test_canonical_runner_uses_single_seeded_artifact_stage_path(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = _state()

    def _fake_answer_stage_runner(*_args, **_kwargs):
        return expected

    monkeypatch.setattr(runtime, "_run_answer_stages_from_supplied_artifacts", _fake_answer_stage_runner)

    actual = runtime.run_canonical_answer_stage_flow(
        llm=object(),
        state=_state(),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
    )

    assert actual is expected


def test_no_parallel_full_turn_seeded_runner_symbol_exists() -> None:
    assert not hasattr(runtime, "_run_full_canonical_turn_from_seeded_artifacts")
