from __future__ import annotations

from dataclasses import dataclass

from testbot.answer_contract_constants import (
    ASSIST_ALTERNATIVES_ANSWER,
    BACKGROUND_INGESTION_PROGRESS_ANSWER,
    CLARIFY_ANSWER,
    DENY_ANSWER,
    FALLBACK_ANSWER,
    NON_KNOWLEDGE_UNCERTAINTY_ANSWER,
    ROUTE_TO_ASK_ANSWER,
)


@dataclass(frozen=True)
class AnswerStageSemanticContract:
    deny_answer: str = DENY_ANSWER
    fallback_answer: str = FALLBACK_ANSWER
    clarify_answer: str = CLARIFY_ANSWER
    route_to_ask_answer: str = ROUTE_TO_ASK_ANSWER
    assist_alternatives_answer: str = ASSIST_ALTERNATIVES_ANSWER
    non_knowledge_uncertainty_answer: str = NON_KNOWLEDGE_UNCERTAINTY_ANSWER
    background_ingestion_progress_answer: str = BACKGROUND_INGESTION_PROGRESS_ANSWER


DEFAULT_ANSWER_STAGE_SEMANTIC_CONTRACT = AnswerStageSemanticContract()


def expected_alignment_decisions_for_final_answer(
    final_answer: str,
    *,
    semantic_contract: AnswerStageSemanticContract = DEFAULT_ANSWER_STAGE_SEMANTIC_CONTRACT,
) -> set[str]:
    if final_answer == semantic_contract.deny_answer:
        return {"deny"}
    if final_answer == semantic_contract.fallback_answer:
        return {"fallback"}
    if final_answer in {
        semantic_contract.clarify_answer,
        semantic_contract.route_to_ask_answer,
        semantic_contract.assist_alternatives_answer,
        semantic_contract.non_knowledge_uncertainty_answer,
        semantic_contract.background_ingestion_progress_answer,
    }:
        return {"allow"}
    return {"allow", "fallback"}

