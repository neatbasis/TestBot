from __future__ import annotations

from dataclasses import dataclass

import arrow

from testbot.behave_support import run_answer_stage_flow as run_canonical_answer_stage_flow
from testbot.pipeline_state import PipelineState
from testbot.time_parse import parse_target_time
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

def test_run_canonical_answer_stage_flow_time_query_uses_fake_clock_and_helsinki() -> None:
    frozen_now = arrow.get("2026-03-10T22:30:00+00:00")
    state = PipelineState(user_input="what is tomorrow?", last_user_message_ts="2026-03-10T22:00:00+00:00")

    updated = run_canonical_answer_stage_flow(
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
    assert updated.invariant_decisions["answer_mode"] == "assist"
    assert updated.invariant_decisions["answer_mode_rationale"]["reason"] == "time_answer"


def test_parse_target_time_maps_ambiguous_temporal_phrases_deterministically() -> None:
    now = arrow.get("2026-03-10T11:00:00+00:00")

    assert parse_target_time("What did I mention earlier this week?", now=now) == now.floor("week")
    assert parse_target_time("What did I mention this morning?", now=now) == now.floor("day").shift(hours=+9)
    assert parse_target_time("What did I mention recently?", now=now) == now.shift(hours=-6)
