from __future__ import annotations

from collections import deque

import pytest

import testbot.behave_support as behave_support
from testbot.entrypoints.runtime_loop import run_chat_loop
from testbot.pipeline_state import PipelineState


class _RuntimeCapabilityStatusStub:
    debug_enabled = False
    debug_verbose = False


class _CapabilitySnapshotStub:
    runtime_capability_status = _RuntimeCapabilityStatusStub()


class _ClockStub:
    class _Now:
        def isoformat(self) -> str:
            return "2026-03-19T00:00:00+00:00"

    def now(self) -> _Now:
        return self._Now()


def test_run_canonical_answer_stage_flow_routes_seeded_inputs_through_canonical_turn_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_pipeline(**kwargs):
        captured.update(kwargs)
        return PipelineState(user_input=kwargs["utterance"], final_answer="canonical"), []

    monkeypatch.setattr(behave_support, "_run_canonical_turn_pipeline_for_behave", _fake_pipeline)

    state = behave_support.run_answer_stage_flow(
        llm=object(),
        state=PipelineState(user_input="hello"),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
    )

    assert state.final_answer == "canonical"
    assert captured["utterance"] == "hello"


def test_chat_loop_routes_raw_utterance_via_canonical_turn_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    from testbot.entrypoints import runtime_loop

    calls: list[tuple[str, str]] = []

    def _fake_pipeline(**kwargs):
        calls.append((kwargs["utterance"], kwargs["io_channel"]))
        return (
            PipelineState(
                user_input=kwargs["utterance"],
                rewritten_query=kwargs["utterance"],
                final_answer="canonical answer",
                confidence_decision={"context_confident": True},
            ),
            [],
        )

    monkeypatch.setattr(runtime_loop, "run_runtime_turn_pipeline", _fake_pipeline)
    monkeypatch.setattr(runtime_loop, "persist_answer_commit", lambda **_kwargs: None)

    utterances = iter(["hello", "stop"])
    outputs: list[str] = []

    run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=_CapabilitySnapshotStub(),
        read_user_utterance=lambda: next(utterances),
        send_assistant_text=outputs.append,
        clock=_ClockStub(),
    )

    assert calls == [("hello", "cli")]
    assert outputs[0] == "canonical answer"
    assert outputs[-1] == "Stopping. Bye."
