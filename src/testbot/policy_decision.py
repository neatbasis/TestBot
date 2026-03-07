from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from testbot.evidence_retrieval import EvidenceBundle, EvidencePosture, RetrievalResult
from testbot.intent_router import IntentType


class DecisionClass(StrEnum):
    ANSWER_FROM_MEMORY = "answer_from_memory"
    ASK_FOR_CLARIFICATION = "ask_for_clarification"
    CONTINUE_REPAIR_RECONSTRUCTION = "continue_repair_reconstruction"
    ANSWER_GENERAL_KNOWLEDGE_LABELED = "answer_general_knowledge_labeled"


@dataclass(frozen=True)
class DecisionObject:
    decision_class: DecisionClass
    retrieval_branch: str
    rationale: str
    reasoning: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalPolicyDecision:
    retrieval_branch: str
    evidence_posture: EvidencePosture
    rationale: str
    reasoning: dict[str, object] = field(default_factory=dict)

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
            reasoning={"empty_evidence": False, "scored_empty": False},
        )

    considered = retrieval_candidates_considered
    if considered is None or considered <= 0:
        posture = EvidencePosture.EMPTY_EVIDENCE
        rationale = "retrieval scan returned no candidates"
    elif (hit_count or 0) <= 0:
        posture = EvidencePosture.SCORED_EMPTY
        rationale = "retrieval produced scored candidates but none survived confidence/rerank"
    else:
        posture = EvidencePosture.SCORED_NON_EMPTY
        rationale = "retrieval produced scored candidates with confident evidence"

    return RetrievalPolicyDecision(
        retrieval_branch=branch,
        evidence_posture=posture,
        rationale=rationale,
        reasoning={
            "empty_evidence": posture is EvidencePosture.EMPTY_EVIDENCE,
            "scored_empty": posture is EvidencePosture.SCORED_EMPTY,
            "retrieval_candidates_considered": considered if considered is not None else 0,
            "hit_count": hit_count if hit_count is not None else 0,
        },
    )


def decide_from_evidence(*, intent: IntentType, retrieval: RetrievalResult, repair_required: bool = False) -> DecisionObject:
    if repair_required:
        return DecisionObject(
            decision_class=DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION,
            retrieval_branch="memory_retrieval",
            rationale="pending repair state requires reconstruction continuation",
            reasoning={"repair_required": True, "evidence_posture": retrieval.evidence_posture.value},
        )

    bundle: EvidenceBundle = retrieval.evidence_bundle
    if retrieval.evidence_posture == EvidencePosture.SCORED_NON_EMPTY and (
        bundle.structured_facts or bundle.episodic_utterances or bundle.source_evidence
    ):
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_FROM_MEMORY,
            retrieval_branch="memory_retrieval",
            rationale="confident evidence bundle supports memory-grounded answer",
            reasoning={"evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
        )

    if intent == IntentType.KNOWLEDGE_QUESTION and retrieval.evidence_posture in {
        EvidencePosture.EMPTY_EVIDENCE,
        EvidencePosture.SCORED_EMPTY,
        EvidencePosture.NOT_REQUESTED,
    }:
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
            retrieval_branch="direct_answer",
            rationale="knowledge question with insufficient memory evidence uses labeled general-knowledge path",
            reasoning={"evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
        )

    return DecisionObject(
        decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
        retrieval_branch="direct_answer",
        rationale="insufficient or conflicting evidence requires clarification",
        reasoning={"evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
    )
