from __future__ import annotations

from dataclasses import dataclass
from typing import Any, MutableMapping


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
    def retrieval_requirement(self) -> dict[str, object]:
        raw = self.values.get("retrieval_requirement")
        return dict(raw) if isinstance(raw, dict) else {}

    @retrieval_requirement.setter
    def retrieval_requirement(self, payload: dict[str, object]) -> None:
        self.values["retrieval_requirement"] = dict(payload)

    def get_bool(self, key: str, *, default: bool = False) -> bool:
        return bool(self.values.get(key, default))

    def setdefault(self, key: str, value: Any) -> Any:
        return self.values.setdefault(key, value)

