from testbot import sat_chatbot_memory_v2 as legacy_runtime
from testbot.answer_contract_constants import (
    ASSIST_ALTERNATIVES_ANSWER,
    CLARIFY_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    ROUTE_TO_ASK_ANSWER,
)


def test_legacy_facade_reexports_canonical_answer_contract_constants() -> None:
    assert legacy_runtime.FALLBACK_ANSWER == FALLBACK_ANSWER
    assert legacy_runtime.DENY_ANSWER == DENY_ANSWER
    assert legacy_runtime.CLARIFY_ANSWER == CLARIFY_ANSWER
    assert legacy_runtime.ROUTE_TO_ASK_ANSWER == ROUTE_TO_ASK_ANSWER
    assert legacy_runtime.ASSIST_ALTERNATIVES_ANSWER == ASSIST_ALTERNATIVES_ANSWER
    assert legacy_runtime.NON_KNOWLEDGE_UNCERTAINTY_ANSWER == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
