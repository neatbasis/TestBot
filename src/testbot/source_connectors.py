from __future__ import annotations

from dataclasses import dataclass
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
