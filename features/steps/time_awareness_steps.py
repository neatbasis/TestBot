from __future__ import annotations

from dataclasses import dataclass

import arrow
from behave import given, then, when

from testbot.intent_router import IntentType, classify_intent
from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import stage_answer


@dataclass(frozen=True)
class FakeClock:
    frozen: arrow.Arrow

    def now(self) -> arrow.Arrow:
        return self.frozen


class _DummyResponse:
    content = ""


class DummyLLM:
    def invoke(self, _msgs):
        return _DummyResponse()


@given("a frozen time in Europe/Helsinki")
def step_given_frozen_time(context) -> None:
    context.timezone = "Europe/Helsinki"
    context.clock = FakeClock(arrow.get("2026-03-10T22:30:00+00:00"))


@when("the user asks how many minutes ago the previous message was")
def step_when_minutes_ago(context) -> None:
    utterance = "how many minutes ago did I ask?"
    assert classify_intent(utterance) is IntentType.TIME_QUERY
    state = PipelineState(user_input=utterance, last_user_message_ts="2026-03-10T22:00:00+00:00")
    context.result_state = stage_answer(
        DummyLLM(),
        state,
        chat_history=[],
        hits=[],
        capability_status="ask_unavailable",
        clock=context.clock,
        timezone=context.timezone,
    )


@when("the user asks what is tomorrow")
def step_when_tomorrow(context) -> None:
    utterance = "what is tomorrow?"
    assert classify_intent(utterance) is IntentType.TIME_QUERY
    state = PipelineState(user_input=utterance, last_user_message_ts="2026-03-10T22:00:00+00:00")
    context.result_state = stage_answer(
        DummyLLM(),
        state,
        chat_history=[],
        hits=[],
        capability_status="ask_unavailable",
        clock=context.clock,
        timezone=context.timezone,
    )


@then("the response should mention elapsed minutes from the previous turn")
def step_then_elapsed(context) -> None:
    assert context.result_state.final_answer == "Your previous user message was 30 minute(s) ago."
    assert context.result_state.invariant_decisions["fallback_action"] == "ANSWER_TIME"


@then("the response should contain the Helsinki tomorrow date")
def step_then_tomorrow(context) -> None:
    assert context.result_state.final_answer == "Tomorrow is 2026-03-12 in Europe/Helsinki."
    assert context.result_state.invariant_decisions["fallback_action"] == "ANSWER_TIME"
