from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from langchain_core.documents import Document


@dataclass(frozen=True)
class SourceItem:
    """Raw item fetched from an external source connector."""

    item_id: str
    content: str
    source_uri: str
    retrieved_at: str
    trust_tier: str
    metadata: dict[str, str]


class SourceConnector(Protocol):
    """Contract for source acquisition connectors.

    Connectors fetch raw source items, normalize each item into a canonical document,
    and maintain a connector-specific cursor/watermark.
    """

    source_type: str

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]: ...

    def normalize(self, item: SourceItem) -> Document: ...

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None: ...


@dataclass(frozen=True)
class FixtureSourceConnector:
    """Deterministic fixture-backed connector for local source-ingestion tests/runtime.

    Cursor semantics are index-based (`"0"`, `"1"`, ...), making lifecycle behavior
    deterministic and easy to assert.
    """

    source_type: str
    fixtures: tuple[SourceItem, ...]

    @classmethod
    def from_json_file(cls, *, source_type: str, fixture_path: str) -> "FixtureSourceConnector":
        raw = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        items = tuple(
            SourceItem(
                item_id=str(entry["item_id"]),
                content=str(entry["content"]),
                source_uri=str(entry["source_uri"]),
                retrieved_at=str(entry["retrieved_at"]),
                trust_tier=str(entry["trust_tier"]),
                metadata={str(k): str(v) for k, v in dict(entry.get("metadata", {})).items()},
            )
            for entry in raw
        )
        return cls(source_type=source_type, fixtures=items)

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceItem]:
        start = int(cursor or "0")
        if start >= len(self.fixtures):
            return []
        return list(self.fixtures[start : start + max(1, limit)])

    def normalize(self, item: SourceItem) -> Document:
        metadata = {
            **item.metadata,
            "doc_id": item.item_id,
            "source_type": self.source_type,
            "source_uri": item.source_uri,
            "retrieved_at": item.retrieved_at,
            "trust_tier": item.trust_tier,
        }
        return Document(id=item.item_id, page_content=item.content, metadata=metadata)

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceItem]) -> str | None:
        if not fetched_items:
            return previous_cursor
        previous_index = int(previous_cursor or "0")
        return str(previous_index + len(fetched_items))
