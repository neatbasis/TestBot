from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any, Mapping


class IntentType(str, Enum):
    """Top-level intent classes used by routing and policy."""

    KNOWLEDGE_QUESTION = "knowledge_question"
    META_CONVERSATION = "meta_conversation"
    CAPABILITIES_HELP = "capabilities_help"
    MEMORY_RECALL = "memory_recall"
    TIME_QUERY = "time_query"
    CONTROL = "control"


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
