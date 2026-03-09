from __future__ import annotations

from dataclasses import dataclass

from testbot.intent_router import IntentType


@dataclass(frozen=True)
class RetrievalRoutingDecision:
    retrieval_branch: str
    requires_retrieval: bool
    reason: str


def is_definitional_query_form(utterance: str) -> bool:
    normalized = (utterance or "").strip().lower()
    return normalized.startswith(("what is", "what are", "what's", "who is", "who are", "who's", "define", "definition of"))


def decide_retrieval_routing(
    *,
    utterance: str,
    intent: IntentType,
    guard_forced_memory_retrieval: bool = False,
) -> RetrievalRoutingDecision:
    if guard_forced_memory_retrieval:
        return RetrievalRoutingDecision(
            retrieval_branch="memory_retrieval",
            requires_retrieval=True,
            reason="identity_continuity_guard_requires_memory_retrieval",
        )

    if intent == IntentType.MEMORY_RECALL:
        return RetrievalRoutingDecision(
            retrieval_branch="memory_retrieval",
            requires_retrieval=True,
            reason="resolved_memory_recall_intent",
        )

    if intent == IntentType.KNOWLEDGE_QUESTION and is_definitional_query_form(utterance):
        return RetrievalRoutingDecision(
            retrieval_branch="memory_retrieval",
            requires_retrieval=True,
            reason="definitional_knowledge_question_prefers_retrieval",
        )

    return RetrievalRoutingDecision(
        retrieval_branch="direct_answer",
        requires_retrieval=False,
        reason="non_memory_or_non_definitional_query",
    )
