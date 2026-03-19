from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping


@dataclass(frozen=True)
class RetrievalRequirement:
    requires_retrieval: bool = False
    reason: str = ""
    retrieval_branch: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> RetrievalRequirement:
        payload = payload or {}
        if isinstance(payload, cls):
            return payload
        known = {
            "requires_retrieval": bool(payload.get("requires_retrieval", False)),
            "reason": str(payload.get("reason") or ""),
            "retrieval_branch": str(payload.get("retrieval_branch") or ""),
        }
        extra = {k: v for k, v in payload.items() if k not in known}
        return cls(extra=extra, **known)

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.extra)
        payload["requires_retrieval"] = self.requires_retrieval
        if self.reason:
            payload["reason"] = self.reason
        if self.retrieval_branch:
            payload["retrieval_branch"] = self.retrieval_branch
        return payload

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


@dataclass
class StageArtifacts:
    """Typed facade over canonical stage artifact map."""

    values: MutableMapping[str, Any]

    @property
    def turn_id(self) -> str:
        return str(self.values.get("turn_id") or "")

    @property
    def pending_ingestion_request_id(self) -> str:
        return str(self.values.get("pending_ingestion_request_id") or "")

    @pending_ingestion_request_id.setter
    def pending_ingestion_request_id(self, value: str) -> None:
        self.values["pending_ingestion_request_id"] = value

    @property
    def retrieval_requirement(self) -> RetrievalRequirement:
        raw = self.values.get("retrieval_requirement")
        return RetrievalRequirement.from_mapping(raw if isinstance(raw, Mapping) else None)

    @retrieval_requirement.setter
    def retrieval_requirement(self, payload: RetrievalRequirement | Mapping[str, object]) -> None:
        self.values["retrieval_requirement"] = RetrievalRequirement.from_mapping(payload).to_dict()

    def get_bool(self, key: str, *, default: bool = False) -> bool:
        return bool(self.values.get(key, default))

    def setdefault(self, key: str, value: Any) -> Any:
        return self.values.setdefault(key, value)
