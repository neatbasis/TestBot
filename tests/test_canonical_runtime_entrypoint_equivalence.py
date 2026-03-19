from __future__ import annotations

from collections import deque

import pytest

from testbot.entrypoints.canonical_runtime_entrypoints import (
    UnsupportedCompatibilityPathError,
    run_canonical_answer_stage_flow_entrypoint,
    run_chat_loop_entrypoint,
)
from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import (
    _canonical_runtime_entrypoint_dependencies,
    run_canonical_answer_stage_flow,
    run_chat_loop,
)


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


def test_answer_stage_compatibility_delegator_matches_canonical_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_state = PipelineState(user_input="hello", final_answer="canonical")

    def _fake_pipeline(**_kwargs):
        return expected_state, []

    monkeypatch.setattr("testbot.sat_chatbot_memory_v2._run_canonical_turn_pipeline", _fake_pipeline)

    compat = run_canonical_answer_stage_flow(
        llm=object(),
        state=PipelineState(user_input="hello"),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
    )

    canonical = run_canonical_answer_stage_flow_entrypoint(
        llm=object(),
        state=PipelineState(user_input="hello"),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        deps=_canonical_runtime_entrypoint_dependencies(),
    )

    assert compat.final_answer == canonical.final_answer == "canonical"


def test_chat_loop_compatibility_delegator_matches_canonical_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    outputs_compat: list[str] = []
    outputs_canonical: list[str] = []

    def _fake_pipeline(**kwargs):
        return PipelineState(user_input=kwargs["utterance"], final_answer="canonical answer"), []

    monkeypatch.setattr("testbot.sat_chatbot_memory_v2._run_canonical_turn_pipeline", _fake_pipeline)
    monkeypatch.setattr("testbot.sat_chatbot_memory_v2.answer_commit_persistence", lambda **_kwargs: None)

    utterances_compat = iter(["hello", "stop"])
    run_chat_loop(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=_CapabilitySnapshotStub(),
        read_user_utterance=lambda: next(utterances_compat),
        send_assistant_text=outputs_compat.append,
        clock=_ClockStub(),
    )

    utterances_canonical = iter(["hello", "stop"])
    run_chat_loop_entrypoint(
        runtime={},
        llm=object(),
        store=object(),
        chat_history=deque(),
        near_tie_delta=0.05,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=_CapabilitySnapshotStub(),
        read_user_utterance=lambda: next(utterances_canonical),
        send_assistant_text=outputs_canonical.append,
        clock=_ClockStub(),
        deps=_canonical_runtime_entrypoint_dependencies(),
    )

    assert outputs_compat == outputs_canonical == ["canonical answer", "Stopping. Bye."]


def test_canonical_entrypoint_rejects_noncanonical_seeded_decision_override() -> None:
    with pytest.raises(UnsupportedCompatibilityPathError, match="selected_decision"):
        run_canonical_answer_stage_flow_entrypoint(
            llm=object(),
            state=PipelineState(user_input="hello"),
            chat_history=deque(),
            hits=[],
            capability_status="ask_unavailable",
            selected_decision=object(),
            deps=_canonical_runtime_entrypoint_dependencies(),
        )


def test_canonical_entrypoint_rejects_noncanonical_timezone_override() -> None:
    with pytest.raises(UnsupportedCompatibilityPathError, match="timezone"):
        run_canonical_answer_stage_flow_entrypoint(
            llm=object(),
            state=PipelineState(user_input="hello"),
            chat_history=deque(),
            hits=[],
            capability_status="ask_unavailable",
            timezone="UTC",
            deps=_canonical_runtime_entrypoint_dependencies(),
        )
