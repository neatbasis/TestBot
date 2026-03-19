from __future__ import annotations

from collections import deque

import pytest

from testbot.pipeline_state import PipelineState
import testbot.sat_chatbot_memory_v2 as runtime


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

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _fake_pipeline)
    monkeypatch.setattr(
        runtime,
        "answer_assemble",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("direct answer-stage path must not be used")),
    )

    state = runtime.run_canonical_answer_stage_flow(
        llm=object(),
        state=PipelineState(user_input="hello"),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
    )

    assert state.final_answer == "canonical"
    assert captured["utterance"] == "hello"


def test_chat_loop_routes_raw_utterance_via_canonical_turn_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
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

    monkeypatch.setattr(runtime, "_run_canonical_turn_pipeline", _fake_pipeline)
    monkeypatch.setattr(
        runtime,
        "run_canonical_answer_stage_flow",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("seeded answer stage flow must not be used")),
    )
    monkeypatch.setattr(runtime, "answer_commit_persistence", lambda **_kwargs: None)

    utterances = iter(["hello", "stop"])
    outputs: list[str] = []

    runtime.run_chat_loop(
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
