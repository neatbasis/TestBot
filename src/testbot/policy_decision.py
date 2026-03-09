from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from testbot.evidence_retrieval import EvidenceBundle, EvidencePosture, RetrievalResult
from testbot.intent_router import IntentType
from testbot.retrieval_routing import decide_retrieval_routing


class DecisionClass(StrEnum):
    ANSWER_FROM_MEMORY = "answer_from_memory"
    ASK_FOR_CLARIFICATION = "ask_for_clarification"
    CONTINUE_REPAIR_RECONSTRUCTION = "continue_repair_reconstruction"
    PENDING_LOOKUP_BACKGROUND_INGESTION = "pending_lookup_background_ingestion"
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


def decide(
    *,
    utterance: str,
    intent: IntentType,
    retrieval_candidates_considered: int | None = None,
    hit_count: int | None = None,
    guard_forced_memory_retrieval: bool = False,
) -> RetrievalPolicyDecision:
    routing = decide_retrieval_routing(
        utterance=utterance,
        intent=intent,
        guard_forced_memory_retrieval=guard_forced_memory_retrieval,
    )
    branch = routing.retrieval_branch
    if branch != "memory_retrieval":
        return RetrievalPolicyDecision(
            retrieval_branch=branch,
            evidence_posture=EvidencePosture.NOT_REQUESTED,
            rationale="non-memory or social intent routed to direct answer policy",
            reasoning={"empty_evidence": False, "scored_empty": False},
        )

    forced_reasoning: dict[str, object] = {}
    if guard_forced_memory_retrieval:
        forced_reasoning["guard_forced_memory_retrieval"] = True

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

    if guard_forced_memory_retrieval:
        rationale = (
            "self-referential identity recall with prior identity continuity artifacts "
            "forces memory retrieval evaluation"
        )

    return RetrievalPolicyDecision(
        retrieval_branch=branch,
        evidence_posture=posture,
        rationale=rationale,
        reasoning={
            "empty_evidence": posture is EvidencePosture.EMPTY_EVIDENCE,
            "scored_empty": posture is EvidencePosture.SCORED_EMPTY,
            "retrieval_candidates_considered": considered if considered is not None else 0,
            "hit_count": hit_count if hit_count is not None else 0,
            **forced_reasoning,
        },
    )


def decide_from_evidence(*, intent: IntentType, retrieval: RetrievalResult, repair_required: bool = False) -> DecisionObject:
    if repair_required and retrieval.evidence_posture == EvidencePosture.EMPTY_EVIDENCE:
        return DecisionObject(
            decision_class=DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION,
            retrieval_branch="memory_retrieval",
            rationale="retrieval required but empty evidence while background ingestion is in progress",
            reasoning={
                "repair_required": True,
                "background_ingestion_in_progress": True,
                "evidence_posture": retrieval.evidence_posture.value,
                **retrieval.reasoning,
            },
        )

    if repair_required:
        return DecisionObject(
            decision_class=DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION,
            retrieval_branch="memory_retrieval",
            rationale="pending repair state requires reconstruction continuation",
            reasoning={"repair_required": True, "evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
        )

    bundle: EvidenceBundle = retrieval.evidence_bundle
    has_policy_records = bool(bundle.records_for_policy())

    if retrieval.evidence_posture == EvidencePosture.SCORED_NON_EMPTY and has_policy_records:
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_FROM_MEMORY,
            retrieval_branch="memory_retrieval",
            rationale="confident evidence bundle supports memory-grounded answer",
            reasoning={"evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
        )

    if intent == IntentType.MEMORY_RECALL:
        if retrieval.evidence_posture == EvidencePosture.EMPTY_EVIDENCE:
            return DecisionObject(
                decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
                retrieval_branch="memory_retrieval",
                rationale="memory recall had no retrievable candidates and requires explicit clarification",
                reasoning={"evidence_posture": retrieval.evidence_posture.value, "empty_vs_scored": "empty_evidence", **retrieval.reasoning},
            )
        if retrieval.evidence_posture == EvidencePosture.SCORED_EMPTY:
            return DecisionObject(
                decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
                retrieval_branch="memory_retrieval",
                rationale="memory recall candidates were scored but all rejected; preserve memory recall with clarifier",
                reasoning={"evidence_posture": retrieval.evidence_posture.value, "empty_vs_scored": "scored_empty", **retrieval.reasoning},
            )
        return DecisionObject(
            decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
            retrieval_branch="direct_answer",
            rationale="memory recall without retrieval request requires clarification",
            reasoning={"evidence_posture": retrieval.evidence_posture.value, "empty_vs_scored": "not_requested", **retrieval.reasoning},
        )

    if intent == IntentType.KNOWLEDGE_QUESTION:
        if retrieval.evidence_posture == EvidencePosture.EMPTY_EVIDENCE:
            rationale = "knowledge question with empty evidence uses labeled general-knowledge path"
            distinction = "empty_evidence"
        elif retrieval.evidence_posture == EvidencePosture.SCORED_EMPTY:
            rationale = "knowledge question with scored-empty evidence uses labeled general-knowledge path"
            distinction = "scored_empty"
        else:
            rationale = "knowledge question without retrieval uses labeled general-knowledge path"
            distinction = "not_requested"
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
            retrieval_branch="direct_answer",
            rationale=rationale,
            reasoning={"evidence_posture": retrieval.evidence_posture.value, "empty_vs_scored": distinction, **retrieval.reasoning},
        )

    if intent == IntentType.META_CONVERSATION:
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
            retrieval_branch="direct_answer",
            rationale="non-knowledge conversational intent remains assistive direct-answer without memory retrieval",
            reasoning={"evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
        )

    return DecisionObject(
        decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
        retrieval_branch="direct_answer",
        rationale="insufficient or conflicting evidence requires clarification",
        reasoning={"evidence_posture": retrieval.evidence_posture.value, **retrieval.reasoning},
    )
