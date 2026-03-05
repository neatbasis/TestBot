from __future__ import annotations

from dataclasses import dataclass

import arrow

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import stage_answer, stage_rerank
from testbot.time_reasoning import elapsed_since_last_user_message, resolve_relative_date


@dataclass(frozen=True)
class FakeClock:
    frozen: arrow.Arrow

    def now(self) -> arrow.Arrow:
        return self.frozen


class _DummyResponse:
    def __init__(self, content: str = "") -> None:
        self.content = content


class DummyLLM:
    def invoke(self, _msgs):
        return _DummyResponse("")


def test_elapsed_since_last_user_message_returns_seconds() -> None:
    now = arrow.get("2026-03-10T10:05:00+00:00")
    assert elapsed_since_last_user_message("2026-03-10T10:00:00+00:00", now) == 300


def test_resolve_relative_date_uses_helsinki_timezone() -> None:
    now = arrow.get("2026-03-10T22:30:00+00:00")
    assert resolve_relative_date("tomorrow", now, "Europe/Helsinki") == "2026-03-12"


def test_stage_rerank_uses_injected_clock_now() -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="what happened")

    updated, _ = stage_rerank(
        state,
        [],
        utterance="what happened",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert updated.confidence_decision["now_ts"] == frozen_now.isoformat()


def test_stage_answer_time_query_uses_fake_clock_and_helsinki() -> None:
    frozen_now = arrow.get("2026-03-10T22:30:00+00:00")
    state = PipelineState(user_input="what is tomorrow?", last_user_message_ts="2026-03-10T22:00:00+00:00")

    updated = stage_answer(
        DummyLLM(),
        state,
        chat_history=[],
        hits=[],
        capability_status="ask_unavailable",
        clock=FakeClock(frozen_now),
        timezone="Europe/Helsinki",
    )

    assert updated.final_answer == "Tomorrow is 2026-03-12 in Europe/Helsinki."
    assert updated.invariant_decisions["fallback_action"] == "ANSWER_TIME"
