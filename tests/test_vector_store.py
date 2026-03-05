from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from testbot.vector_store import PromotingMemoryStore


@dataclass
class FakeStore:
    docs: list[Document]

    def add_documents(self, documents: list[Document]) -> None:
        self.docs.extend(documents)

    def similarity_search_with_score(self, query: str, k: int = 4):
        if not self.docs:
            return []
        return [(d, 0.9) for d in self.docs[:k]]


def test_promoting_memory_store_queries_fallback_and_promotes() -> None:
    primary = FakeStore(docs=[])
    fallback = FakeStore(docs=[Document(id="1", page_content="known fact", metadata={"ts": "2026-01-01"})])
    store = PromotingMemoryStore(primary=primary, fallback=fallback, promote_top_k=1)

    hits = store.similarity_search_with_score("known", k=2)

    assert len(hits) == 1
    assert hits[0][0].id == "1"
    assert primary.docs
    assert primary.docs[0].metadata["promoted_from"] == "elasticsearch"
