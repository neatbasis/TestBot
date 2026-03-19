from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


PortMetadata = dict[str, object]


@dataclass(frozen=True)
class PortDocument:
    doc_id: str
    content: str
    metadata: PortMetadata = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredPortDocument:
    document: PortDocument
    score: float


@dataclass(frozen=True)
class MemorySearchQuery:
    query: str
    k: int = 4
    exclude_doc_ids: set[str] = field(default_factory=set)
    exclude_source_ids: set[str] = field(default_factory=set)
    exclude_turn_scoped_ids: set[str] = field(default_factory=set)
    segment_ids: set[str] = field(default_factory=set)
    segment_types: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class SourceRecord:
    item_id: str
    content: str
    source_uri: str
    retrieved_at: str
    trust_tier: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelPrompt:
    content: str


@dataclass(frozen=True)
class ModelResponse:
    content: str
    metadata: dict[str, object] = field(default_factory=dict)


class VectorStore(Protocol):
    def add_documents(self, documents: list[PortDocument]) -> None: ...

    def similarity_search(self, query: MemorySearchQuery) -> list[ScoredPortDocument]: ...


class MemoryRepository(Protocol):
    def add_memory_records(self, records: list[PortDocument]) -> None: ...

    def search_memory_records(self, query: MemorySearchQuery) -> list[ScoredPortDocument]: ...




class MemoryStorePort(MemoryRepository, Protocol):
    """Narrow runtime memory-storage port for non-adapter layers."""

    def add_documents(self, documents: list[object]) -> None: ...

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        *,
        exclude_doc_ids: set[str] | None = None,
        exclude_source_ids: set[str] | None = None,
        exclude_turn_scoped_ids: set[str] | None = None,
        segment_ids: set[str] | None = None,
        segment_types: set[str] | None = None,
    ) -> list[tuple[object, float]]: ...

class LanguageModel(Protocol):
    def invoke(self, prompt: object) -> object: ...


class SourceConnector(Protocol):
    source_type: str

    def fetch(self, *, cursor: str | None, limit: int = 50) -> list[SourceRecord]: ...

    def normalize(self, item: SourceRecord) -> PortDocument: ...

    def update_cursor(self, *, previous_cursor: str | None, fetched_items: list[SourceRecord]) -> str | None: ...
