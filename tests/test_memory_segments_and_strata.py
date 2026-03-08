from __future__ import annotations

from langchain_core.documents import Document

from testbot.evidence_retrieval import build_evidence_bundle_from_docs_and_scores
from testbot.memory_strata import SegmentType, derive_segment_descriptor
from testbot.vector_store import InMemoryMemoryStore


class _StubVectorStore:
    def __init__(self, docs: list[Document]) -> None:
        self._docs = docs

    def add_documents(self, documents: list[Document]) -> None:
        self._docs.extend(documents)

    def similarity_search_with_score(self, _query: str, k: int = 4) -> list[tuple[Document, float]]:
        return [(doc, 0.9) for doc in self._docs[:k]]


def test_segment_creation_keeps_multi_turn_continuity() -> None:
    first = derive_segment_descriptor(utterance="My name is Sebastian", has_dialogue_state=True)
    second = derive_segment_descriptor(
        utterance="My name is Sebastian and I prefer tea",
        prior_descriptor=first,
        has_dialogue_state=True,
    )

    assert first.segment_type == SegmentType.SELF_PROFILE
    assert second.segment_id == first.segment_id


def test_retrieval_can_filter_by_segment_constraints() -> None:
    target_segment = derive_segment_descriptor(utterance="What was my sleep note yesterday?")
    other_segment = derive_segment_descriptor(utterance="Book a table tonight")
    docs = [
        Document(
            id="sleep-1",
            page_content="sleep continuity",
            metadata={"doc_id": "sleep-1", "segment_id": target_segment.segment_id, "segment_type": target_segment.segment_type.value},
        ),
        Document(
            id="task-1",
            page_content="reservation continuity",
            metadata={"doc_id": "task-1", "segment_id": other_segment.segment_id, "segment_type": other_segment.segment_type.value},
        ),
    ]
    store = InMemoryMemoryStore(_StubVectorStore(docs))

    hits = store.similarity_search_with_score(
        "sleep",
        k=5,
        segment_ids={target_segment.segment_id},
        segment_types={target_segment.segment_type.value},
    )

    assert [doc.id for doc, _ in hits] == ["sleep-1"]


def test_semantic_memory_precedence_beats_raw_utterance_when_both_exist() -> None:
    segment = derive_segment_descriptor(utterance="What's my name?")
    docs_and_scores = [
        (
            Document(
                id="semantic-name",
                page_content="name=Sebastian",
                metadata={"type": "profile_fact", "memory_stratum": "semantic", "segment_id": segment.segment_id},
            ),
            0.8,
        ),
        (
            Document(
                id="raw-utterance-name",
                page_content="My name might be...",
                metadata={"type": "user_utterance", "memory_stratum": "episodic", "segment_id": segment.segment_id},
            ),
            0.95,
        ),
    ]

    bundle = build_evidence_bundle_from_docs_and_scores(docs_and_scores)

    assert [record.ref_id for record in bundle.structured_facts] == ["semantic-name"]
    assert bundle.episodic_utterances == ()
