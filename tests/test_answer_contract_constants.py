from testbot.answer_contract_constants import (
    ASSIST_ALTERNATIVES_ANSWER,
    BACKGROUND_INGESTION_PROGRESS_ANSWER,
    CLARIFY_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    ROUTE_TO_ASK_ANSWER,
)
from testbot.logic import alignment
from testbot import stage_transitions


def test_alignment_and_stage_transition_use_canonical_answer_contract_constants() -> None:
    assert alignment.FALLBACK_ANSWER == FALLBACK_ANSWER
    assert alignment.DENY_ANSWER == DENY_ANSWER
    assert alignment.CLARIFY_ANSWER == CLARIFY_ANSWER
    assert alignment.ROUTE_TO_ASK_ANSWER == ROUTE_TO_ASK_ANSWER
    assert alignment.ASSIST_ALTERNATIVES_ANSWER == ASSIST_ALTERNATIVES_ANSWER
    assert alignment.NON_KNOWLEDGE_UNCERTAINTY_ANSWER == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert alignment.BACKGROUND_INGESTION_PROGRESS_ANSWER == BACKGROUND_INGESTION_PROGRESS_ANSWER

    assert stage_transitions.FALLBACK_ANSWER == FALLBACK_ANSWER
    assert stage_transitions.DENY_ANSWER == DENY_ANSWER
    assert stage_transitions.ASSIST_ALTERNATIVES_ANSWER == ASSIST_ALTERNATIVES_ANSWER
    assert stage_transitions.NON_KNOWLEDGE_UNCERTAINTY_ANSWER == NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    assert stage_transitions.BACKGROUND_INGESTION_PROGRESS_ANSWER == BACKGROUND_INGESTION_PROGRESS_ANSWER
