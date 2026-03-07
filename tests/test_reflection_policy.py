from __future__ import annotations

import pytest

from testbot.answer_policy import AnswerPolicyInput, resolve_answer_routing
from testbot.reflection_policy import decide_fallback_action


@pytest.mark.parametrize(
    ("intent", "memory_hit", "ambiguity", "capability_status", "expected"),
    [
        ("time_query", True, True, "ask_available", "ANSWER_TIME"),
        ("time_query", False, False, "ask_unavailable", "ANSWER_TIME"),
        ("memory_recall", True, True, "ask_available", "ROUTE_TO_ASK"),
        ("memory_recall", True, True, "ask_unavailable", "ASK_CLARIFYING_QUESTION"),
        ("memory_recall", True, False, "ask_available", "ANSWER_GENERAL_KNOWLEDGE"),
        ("memory_recall", True, False, "ask_unavailable", "ANSWER_GENERAL_KNOWLEDGE"),
        ("memory_recall", False, True, "ask_available", "ROUTE_TO_ASK"),
        ("memory_recall", False, True, "ask_unavailable", "ASK_CLARIFYING_QUESTION"),
        ("memory_recall", False, False, "ask_available", "OFFER_CAPABILITY_ALTERNATIVES"),
        ("memory_recall", False, False, "ask_unavailable", "OFFER_CAPABILITY_ALTERNATIVES"),
        ("non_memory", True, True, "ask_available", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", True, True, "ask_unavailable", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", True, False, "ask_available", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", True, False, "ask_unavailable", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", False, True, "ask_available", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", False, True, "ask_unavailable", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", False, False, "ask_available", "ANSWER_GENERAL_KNOWLEDGE"),
        ("non_memory", False, False, "ask_unavailable", "ANSWER_GENERAL_KNOWLEDGE"),
    ],
)
def test_decide_fallback_action_policy_rows(
    intent: str,
    memory_hit: bool,
    ambiguity: bool,
    capability_status: str,
    expected: str,
) -> None:
    assert (
        decide_fallback_action(
            intent=intent,
            memory_hit=memory_hit,
            ambiguity=ambiguity,
            capability_status=capability_status,
        )
        == expected
    )


def test_low_source_confidence_non_memory_returns_unknown_fallback_even_with_memory_hit() -> None:
    assert decide_fallback_action(
        intent="non_memory",
        memory_hit=True,
        ambiguity=False,
        capability_status="ask_unavailable",
        source_confidence=0.2,
    ) == "ANSWER_UNKNOWN"


def test_low_source_confidence_does_not_override_memory_recall_policy() -> None:
    assert decide_fallback_action(
        intent="memory_recall",
        memory_hit=False,
        ambiguity=False,
        capability_status="ask_unavailable",
        source_confidence=0.2,
    ) == "OFFER_CAPABILITY_ALTERNATIVES"


def test_source_confidence_does_not_override_time_query() -> None:
    assert decide_fallback_action(
        intent="time_query",
        memory_hit=False,
        ambiguity=False,
        capability_status="ask_unavailable",
        source_confidence=0.1,
    ) == "ANSWER_TIME"


def test_answer_routing_parity_with_reflection_fallback_matrix() -> None:
    for intent in ("memory_recall", "non_memory", "time_query"):
        for memory_hit in (False, True):
            for ambiguity in (False, True):
                for capability_status in ("ask_available", "ask_unavailable"):
                    confidence_decision = {
                        "context_confident": memory_hit,
                        "ambiguity_detected": ambiguity,
                    }
                    policy = resolve_answer_routing(
                        AnswerPolicyInput(
                            intent=intent,
                            confidence_decision=confidence_decision,
                            capability_status=capability_status,
                        )
                    )
                    expected = decide_fallback_action(
                        intent=intent,
                        memory_hit=memory_hit,
                        ambiguity=ambiguity,
                        capability_status=capability_status,
                    )
                    assert policy.fallback_action == expected


def test_answer_routing_low_source_confidence_parity_for_non_memory() -> None:
    policy = resolve_answer_routing(
        AnswerPolicyInput(
            intent="non_memory",
            confidence_decision={"context_confident": True, "ambiguity_detected": False},
            capability_status="ask_unavailable",
            source_confidence=0.2,
        )
    )

    assert policy.fallback_action == "ANSWER_UNKNOWN"
    assert policy.canonical_response_token == "NON_KNOWLEDGE_UNCERTAINTY_ANSWER"
