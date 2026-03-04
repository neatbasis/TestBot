from __future__ import annotations

import pytest

from testbot.reflection_policy import decide_fallback_action


@pytest.mark.parametrize(
    ("intent", "memory_hit", "ambiguity", "capability_status", "expected"),
    [
        ("memory_recall", True, True, "ask_available", "ROUTE_TO_ASK"),
        ("memory_recall", True, True, "ask_unavailable", "ASK_CLARIFYING_QUESTION"),
        ("memory_recall", True, False, "ask_available", "ANSWER_GENERAL_KNOWLEDGE"),
        ("memory_recall", True, False, "ask_unavailable", "ANSWER_GENERAL_KNOWLEDGE"),
        ("memory_recall", False, True, "ask_available", "ROUTE_TO_ASK"),
        ("memory_recall", False, True, "ask_unavailable", "ASK_CLARIFYING_QUESTION"),
        ("memory_recall", False, False, "ask_available", "EXACT_MEMORY_FALLBACK"),
        ("memory_recall", False, False, "ask_unavailable", "EXACT_MEMORY_FALLBACK"),
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
