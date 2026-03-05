from __future__ import annotations

from collections import deque

from behave import given, then, when
from langchain_core.documents import Document

from testbot.intent_router import IntentType, classify_intent
from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import stage_answer


class _FailIfInvokedLLM:
    def invoke(self, _msgs):  # pragma: no cover - should never be reached in this scenario
        raise AssertionError("LLM should not be called for capabilities-help responses")


@given('a capabilities help prompt "{prompt}"')
def step_given_capabilities_prompt(context, prompt: str) -> None:
    context.prompt = prompt


@when("the stage answer flow handles the prompt with and without memory hits")
def step_when_stage_answer_handles(context) -> None:
    context.intent = classify_intent(context.prompt)
    base_state = PipelineState(
        user_input=context.prompt,
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )
    context.empty_memory_state = stage_answer(
        _FailIfInvokedLLM(),
        base_state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=None,
    )
    context.with_memory_state = stage_answer(
        _FailIfInvokedLLM(),
        base_state,
        chat_history=deque(),
        hits=[Document(page_content="Previous memory detail", metadata={"doc_id": "d1", "ts": "2024-01-01T00:00:00Z"})],
        capability_status="ask_available",
        clock=None,
    )


@then("the prompt is classified as capabilities help intent")
def step_then_classified(context) -> None:
    assert context.intent is IntentType.CAPABILITIES_HELP


@then("both answers return the stable capability summary")
def step_then_stable_summary(context) -> None:
    assert context.empty_memory_state.final_answer == context.with_memory_state.final_answer


@then('the summary includes "{expected}"')
def step_then_summary_includes(context, expected: str) -> None:
    assert expected in context.empty_memory_state.final_answer
