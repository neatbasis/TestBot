from __future__ import annotations

from collections import deque

from behave import given, then, when
from langchain_core.documents import Document

from testbot.intent_router import IntentType, classify_intent
from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import RuntimeCapabilityStatus, run_answer_stage_flow


class _FailIfInvokedLLM:
    def invoke(self, _msgs):  # pragma: no cover - should never be reached in this scenario
        raise AssertionError("LLM should not be called for capabilities-help responses")


@given('a capabilities help prompt "{prompt}"')
def step_given_capabilities_prompt(context, prompt: str) -> None:
    context.prompt = prompt


@when("the stage answer flow handles capabilities under HA unavailable with CLI fallback")
def step_when_ha_unavailable_cli(context) -> None:
    context.intent = classify_intent(context.prompt)
    state = PipelineState(
        user_input=context.prompt,
        classified_intent=IntentType.CAPABILITIES_HELP.value,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )
    context.answer_state = run_answer_stage_flow(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=[Document(page_content="Previous memory detail", metadata={"doc_id": "d1", "ts": "2024-01-01T00:00:00Z"})],
        capability_status="ask_unavailable",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=False,
            effective_mode="cli",
            requested_mode="auto",
            daemon_mode=False,
            fallback_reason="satellite connection is unavailable",
            memory_backend="in_memory",
            debug_enabled=False,
            debug_verbose=False,
            text_clarification_available=True,
            satellite_ask_available=False,
        ),
        clock=None,
    )


@when("the stage answer flow handles capabilities under HA available with satellite enabled")
def step_when_ha_available_satellite(context) -> None:
    context.intent = classify_intent(context.prompt)
    state = PipelineState(
        user_input=context.prompt,
        classified_intent=IntentType.CAPABILITIES_HELP.value,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )
    context.answer_state = run_answer_stage_flow(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_available",
        runtime_capability_status=RuntimeCapabilityStatus(
            ollama_available=True,
            ha_available=True,
            effective_mode="satellite",
            requested_mode="satellite",
            daemon_mode=False,
            fallback_reason=None,
            memory_backend="elasticsearch",
            debug_enabled=True,
            debug_verbose=False,
            text_clarification_available=True,
            satellite_ask_available=True,
        ),
        clock=None,
    )


@then("the prompt is classified as capabilities help intent")
def step_then_classified(context) -> None:
    assert context.intent is IntentType.CAPABILITIES_HELP


@then('the answer includes "{expected}"')
def step_then_answer_includes(context, expected: str) -> None:
    assert expected in context.answer_state.final_answer


@then('the answer excludes "{unexpected}"')
def step_then_answer_excludes(context, unexpected: str) -> None:
    assert unexpected not in context.answer_state.final_answer
