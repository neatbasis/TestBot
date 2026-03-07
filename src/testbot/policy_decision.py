from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from testbot.intent_router import IntentType


class EvidencePosture(StrEnum):
    NOT_REQUESTED = "not_requested"
    EMPTY_EVIDENCE = "empty_evidence"
    SCORED_EMPTY = "scored_empty"
    SCORED_NON_EMPTY = "scored_non_empty"


@dataclass(frozen=True)
class RetrievalPolicyDecision:
    retrieval_branch: str
    evidence_posture: EvidencePosture
    rationale: str

    @property
    def requires_retrieval(self) -> bool:
        return self.retrieval_branch == "memory_retrieval"


def _is_definitional_query_form(utterance: str) -> bool:
    normalized = (utterance or "").strip().lower()
    return normalized.startswith(("what is", "what are", "what's", "who is", "who are", "who's", "define", "definition of"))


def _select_branch(*, utterance: str, intent: IntentType) -> str:
    if intent == IntentType.MEMORY_RECALL:
        return "memory_retrieval"
    if intent == IntentType.KNOWLEDGE_QUESTION and _is_definitional_query_form(utterance):
        return "memory_retrieval"
    return "direct_answer"


def decide(
    *,
    utterance: str,
    intent: IntentType,
    retrieval_candidates_considered: int | None = None,
    hit_count: int | None = None,
) -> RetrievalPolicyDecision:
    branch = _select_branch(utterance=utterance, intent=intent)
    if branch != "memory_retrieval":
        return RetrievalPolicyDecision(
            retrieval_branch=branch,
            evidence_posture=EvidencePosture.NOT_REQUESTED,
            rationale="non-memory or social intent routed to direct answer policy",
        )

    considered = retrieval_candidates_considered
    if considered is None:
        posture = EvidencePosture.EMPTY_EVIDENCE
        rationale = "retrieval enabled; awaiting evidence scan"
    elif considered <= 0:
        posture = EvidencePosture.EMPTY_EVIDENCE
        rationale = "retrieval scan returned no candidates"
    elif (hit_count or 0) <= 0:
        posture = EvidencePosture.SCORED_EMPTY
        rationale = "retrieval produced scored candidates but none survived confidence/rerank"
    else:
        posture = EvidencePosture.SCORED_NON_EMPTY
        rationale = "retrieval produced scored candidates with confident evidence"

    return RetrievalPolicyDecision(retrieval_branch=branch, evidence_posture=posture, rationale=rationale)
