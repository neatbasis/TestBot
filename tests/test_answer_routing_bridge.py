from __future__ import annotations

import pytest

from testbot.policy_decision import DecisionClass, DecisionObject
from testbot.sat_chatbot_memory_v2 import resolve_answer_routing_from_decision_object


@pytest.mark.parametrize(
    ("decision_class", "expected_action", "expected_token", "expected_clarification"),
    [
        (DecisionClass.ANSWER_FROM_MEMORY, "ANSWER_FROM_MEMORY", "LLM_DRAFT", False),
        (DecisionClass.ASK_FOR_CLARIFICATION, "ASK_CLARIFYING_QUESTION", "PARTIAL_MEMORY_CLARIFIER", True),
        (DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION, "ASK_CLARIFYING_QUESTION", "PARTIAL_MEMORY_CLARIFIER", True),
        (
            DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION,
            "ANSWER_UNKNOWN",
            "NON_KNOWLEDGE_UNCERTAINTY_ANSWER",
            False,
        ),
        (DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED, "ANSWER_GENERAL_KNOWLEDGE", "LLM_DRAFT", False),
    ],
)
def test_resolve_answer_routing_from_decision_object_covers_all_current_decision_classes(
    decision_class: DecisionClass,
    expected_action: str,
    expected_token: str,
    expected_clarification: bool,
) -> None:
    decision = DecisionObject(
        decision_class=decision_class,
        retrieval_branch="memory_retrieval",
        rationale="test",
    )

    routing = resolve_answer_routing_from_decision_object(decision, capability_status="ask_unavailable")

    assert routing.fallback_action == expected_action
    assert routing.canonical_response_token == expected_token
    assert routing.clarification_allowed is expected_clarification


def test_resolve_answer_routing_from_decision_object_raises_for_unsupported_decision_class() -> None:
    decision = DecisionObject(
        decision_class="unsupported_decision_class",  # type: ignore[arg-type]
        retrieval_branch="direct_answer",
        rationale="test",
    )

    with pytest.raises(ValueError, match="Unsupported DecisionClass"):
        resolve_answer_routing_from_decision_object(decision, capability_status="ask_unavailable")
