from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

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
class DecisionReasoning:
    evidence_posture: str = ""
    empty_vs_scored: str = ""
    repair_required: bool | None = None
    background_ingestion_in_progress: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> DecisionReasoning:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known = {
            "evidence_posture": str(payload.get("evidence_posture") or ""),
            "empty_vs_scored": str(payload.get("empty_vs_scored") or ""),
            "repair_required": bool(payload["repair_required"]) if payload.get("repair_required") is not None else None,
            "background_ingestion_in_progress": (
                bool(payload["background_ingestion_in_progress"])
                if payload.get("background_ingestion_in_progress") is not None
                else None
            ),
        }
        extra = {k: v for k, v in payload.items() if k not in known}
        return cls(extra=extra, **known)

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.extra)
        if self.evidence_posture:
            payload["evidence_posture"] = self.evidence_posture
        if self.empty_vs_scored:
            payload["empty_vs_scored"] = self.empty_vs_scored
        if self.repair_required is not None:
            payload["repair_required"] = self.repair_required
        if self.background_ingestion_in_progress is not None:
            payload["background_ingestion_in_progress"] = self.background_ingestion_in_progress
        return payload

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self):
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

    def keys(self):
        return self.to_dict().keys()

    def items(self):
        return self.to_dict().items()

    def values(self):
        return self.to_dict().values()


@dataclass(frozen=True)
class DecisionObject:
    decision_class: DecisionClass
    retrieval_branch: str
    rationale: str
    reasoning: DecisionReasoning | dict[str, object] = field(default_factory=DecisionReasoning)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reasoning", DecisionReasoning.from_mapping(self.reasoning))


@dataclass(frozen=True)
class RetrievalReasoning:
    empty_evidence: bool = False
    scored_empty: bool = False
    retrieval_candidates_considered: int = 0
    hit_count: int = 0
    guard_forced_memory_retrieval: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> RetrievalReasoning:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known = {
            "empty_evidence": bool(payload.get("empty_evidence", False)),
            "scored_empty": bool(payload.get("scored_empty", False)),
            "retrieval_candidates_considered": int(payload.get("retrieval_candidates_considered", 0) or 0),
            "hit_count": int(payload.get("hit_count", 0) or 0),
            "guard_forced_memory_retrieval": bool(payload.get("guard_forced_memory_retrieval", False)),
        }
        extra = {k: v for k, v in payload.items() if k not in known}
        return cls(extra=extra, **known)

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.extra)
        payload["empty_evidence"] = self.empty_evidence
        payload["scored_empty"] = self.scored_empty
        payload["retrieval_candidates_considered"] = self.retrieval_candidates_considered
        payload["hit_count"] = self.hit_count
        if self.guard_forced_memory_retrieval:
            payload["guard_forced_memory_retrieval"] = self.guard_forced_memory_retrieval
        return payload

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self):
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

    def keys(self):
        return self.to_dict().keys()

    def items(self):
        return self.to_dict().items()

    def values(self):
        return self.to_dict().values()


@dataclass(frozen=True)
class RetrievalPolicyDecision:
    retrieval_branch: str
    evidence_posture: EvidencePosture
    rationale: str
    reasoning: RetrievalReasoning | dict[str, object] = field(default_factory=RetrievalReasoning)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reasoning", RetrievalReasoning.from_mapping(self.reasoning))

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
            reasoning=RetrievalReasoning().to_dict(),
        )

    forced_reasoning: dict[str, Any] = {}
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
        reasoning=RetrievalReasoning.from_mapping(
            {
                "empty_evidence": posture is EvidencePosture.EMPTY_EVIDENCE,
                "scored_empty": posture is EvidencePosture.SCORED_EMPTY,
                "retrieval_candidates_considered": considered if considered is not None else 0,
                "hit_count": hit_count if hit_count is not None else 0,
                **forced_reasoning,
            }
        ).to_dict(),
    )


def decide_from_evidence(*, intent: IntentType, retrieval: RetrievalResult, repair_required: bool = False) -> DecisionObject:
    if repair_required and retrieval.evidence_posture == EvidencePosture.EMPTY_EVIDENCE:
        return DecisionObject(
            decision_class=DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION,
            retrieval_branch="memory_retrieval",
            rationale="retrieval required but empty evidence while background ingestion is in progress",
            reasoning=DecisionReasoning.from_mapping(
                {
                    "repair_required": True,
                    "background_ingestion_in_progress": True,
                    "evidence_posture": retrieval.evidence_posture.value,
                    **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                }
            ).to_dict(),
        )

    if repair_required:
        return DecisionObject(
            decision_class=DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION,
            retrieval_branch="memory_retrieval",
            rationale="pending repair state requires reconstruction continuation",
            reasoning=DecisionReasoning.from_mapping(
                {
                    "repair_required": True,
                    "evidence_posture": retrieval.evidence_posture.value,
                    **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                }
            ).to_dict(),
        )

    bundle: EvidenceBundle = retrieval.evidence_bundle
    has_policy_records = bool(bundle.records_for_policy())

    if retrieval.evidence_posture == EvidencePosture.SCORED_NON_EMPTY and has_policy_records:
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_FROM_MEMORY,
            retrieval_branch="memory_retrieval",
            rationale="confident evidence bundle supports memory-grounded answer",
            reasoning=DecisionReasoning.from_mapping(
                {
                    "evidence_posture": retrieval.evidence_posture.value,
                    **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                }
            ).to_dict(),
        )

    if intent == IntentType.MEMORY_RECALL:
        if retrieval.evidence_posture == EvidencePosture.EMPTY_EVIDENCE:
            return DecisionObject(
                decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
                retrieval_branch="memory_retrieval",
                rationale="memory recall had no retrievable candidates and requires explicit clarification",
                reasoning=DecisionReasoning.from_mapping(
                    {
                        "evidence_posture": retrieval.evidence_posture.value,
                        "empty_vs_scored": "empty_evidence",
                        **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                    }
                ).to_dict(),
            )
        if retrieval.evidence_posture == EvidencePosture.SCORED_EMPTY:
            return DecisionObject(
                decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
                retrieval_branch="memory_retrieval",
                rationale="memory recall candidates were scored but all rejected; preserve memory recall with clarifier",
                reasoning=DecisionReasoning.from_mapping(
                    {
                        "evidence_posture": retrieval.evidence_posture.value,
                        "empty_vs_scored": "scored_empty",
                        **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                    }
                ).to_dict(),
            )
        return DecisionObject(
            decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
            retrieval_branch="direct_answer",
            rationale="memory recall without retrieval request requires clarification",
            reasoning=DecisionReasoning.from_mapping(
                {
                    "evidence_posture": retrieval.evidence_posture.value,
                    "empty_vs_scored": "not_requested",
                    **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                }
            ).to_dict(),
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
            reasoning=DecisionReasoning.from_mapping(
                {
                    "evidence_posture": retrieval.evidence_posture.value,
                    "empty_vs_scored": distinction,
                    **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict(),
                }
            ).to_dict(),
        )

    if intent == IntentType.META_CONVERSATION:
        return DecisionObject(
            decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
            retrieval_branch="direct_answer",
            rationale="non-knowledge conversational intent remains assistive direct-answer without memory retrieval",
            reasoning=DecisionReasoning.from_mapping(
                {"evidence_posture": retrieval.evidence_posture.value, **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict()}
            ).to_dict(),
        )

    return DecisionObject(
        decision_class=DecisionClass.ASK_FOR_CLARIFICATION,
        retrieval_branch="direct_answer",
        rationale="insufficient or conflicting evidence requires clarification",
        reasoning=DecisionReasoning.from_mapping(
            {"evidence_posture": retrieval.evidence_posture.value, **RetrievalReasoning.from_mapping(retrieval.reasoning).to_dict()}
        ).to_dict(),
    )
