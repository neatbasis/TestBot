from __future__ import annotations

from dataclasses import dataclass

import arrow
from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import run_canonical_answer_stage_flow, stage_rerank
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


def test_parse_target_time_maps_ambiguous_temporal_phrases_deterministically() -> None:
    now = arrow.get("2026-03-10T11:00:00+00:00")

    assert parse_target_time("What did I mention earlier this week?", now=now) == now.floor("week")
    assert parse_target_time("What did I mention this morning?", now=now) == now.floor("day").shift(hours=+9)
    assert parse_target_time("What did I mention recently?", now=now) == now.shift(hours=-6)


def test_stage_rerank_pronoun_elapsed_time_emits_anchor_and_delta() -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="How long ago was it?")
    docs_and_scores = [
        (
            Document(
                id="mem-1",
                page_content="You mentioned it before",
                metadata={"doc_id": "mem-1", "type": "user_utterance", "ts": "2026-03-10T11:30:00+00:00"},
            ),
            0.82,
        )
    ]

    updated, hits = stage_rerank(
        state,
        docs_and_scores,
        utterance="How long ago was it?",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert hits
    assert updated.confidence_decision["anaphora_detected"] is True
    assert updated.confidence_decision["selected_anchor_doc_id"] == "mem-1"
    assert updated.confidence_decision["selected_anchor_ts"] == "2026-03-10T11:30:00+00:00"
    assert updated.confidence_decision["computed_delta_raw_seconds"] == 1800
    assert updated.confidence_decision["computed_delta_humanized"] == "30 minutes ago"


def test_stage_rerank_yesterday_window_filters_candidates() -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="What happened yesterday?")
    docs_and_scores = [
        (
            Document(
                id="yesterday-doc",
                page_content="Yesterday note",
                metadata={"doc_id": "yesterday-doc", "type": "user_utterance", "ts": "2026-03-09T08:00:00+00:00"},
            ),
            0.70,
        ),
        (
            Document(
                id="today-doc",
                page_content="Today note",
                metadata={"doc_id": "today-doc", "type": "user_utterance", "ts": "2026-03-10T08:00:00+00:00"},
            ),
            0.95,
        ),
    ]

    updated, hits = stage_rerank(
        state,
        docs_and_scores,
        utterance="What happened yesterday?",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert [doc.id for doc in hits] == ["yesterday-doc"]
    assert updated.confidence_decision["time_window"] == "yesterday"
    assert updated.confidence_decision["window_start"].startswith("2026-03-09T00:00:00")
