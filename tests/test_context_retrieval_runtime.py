from __future__ import annotations

import arrow
from langchain_core.documents import Document

from testbot.application.services import context_retrieval_runtime
from testbot.pipeline_state import CandidateFactsArtifact, PipelineState
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.ports import MemorySearchQuery, PortDocument, ScoredPortDocument


def test_should_force_memory_retrieval_for_identity_recall_true_on_commit_anchor() -> None:
    prior_state = PipelineState(
        user_input="hello",
        candidate_facts=CandidateFactsArtifact(facts=[]),
    )

    assert context_retrieval_runtime.should_force_memory_retrieval_for_identity_recall(
        utterance="who am i?",
        prior_state=prior_state,
        continuity_evidence=("commit.confirmed_user_facts:user_name",),
        context_history_anchors=(),
    )


def test_should_force_memory_retrieval_for_identity_recall_false_for_non_recall_utterance() -> None:
    prior_state = PipelineState(
        user_input="my name is sam",
        candidate_facts=CandidateFactsArtifact(facts=[{"key": "user_name", "value": "sam"}]),
    )

    assert not context_retrieval_runtime.should_force_memory_retrieval_for_identity_recall(
        utterance="tell me a joke",
        prior_state=prior_state,
        continuity_evidence=(),
        context_history_anchors=(),
    )


def test_retrieval_input_document_conversion_round_trip() -> None:
    original = Document(id="doc-1", page_content="hello", metadata={"doc_id": "doc-1", "ts": "2026-03-29T00:00:00+00:00"})

    as_record = context_retrieval_runtime.retrieval_input_from_document(original, score=0.42)
    roundtrip = context_retrieval_runtime.document_from_retrieval_input(as_record)

    assert isinstance(as_record, RetrievalInputRecord)
    assert as_record.ref_id == "doc-1"
    assert as_record.score == 0.42
    assert roundtrip.id == "doc-1"
    assert roundtrip.page_content == "hello"
    assert roundtrip.metadata["ts"] == "2026-03-29T00:00:00+00:00"


def test_stage_retrieve_for_turn_service_uses_injected_stage_function() -> None:
    state = PipelineState(user_input="who am i?", rewritten_query="who am i?")
    observed: dict[str, object] = {}

    def _fake_stage_retrieve(store, pipeline_state, **kwargs):
        observed["store"] = store
        observed["state"] = pipeline_state
        observed["kwargs"] = kwargs
        return pipeline_state, [(Document(id="doc-1", page_content="hello", metadata={"doc_id": "doc-1"}), 0.9)]

    next_state, hits = context_retrieval_runtime.stage_retrieve_for_turn_service(
        object(),
        state,
        stage_retrieve_fn=_fake_stage_retrieve,
        exclude_doc_ids={"a"},
    )

    assert next_state is state
    assert observed["kwargs"]["exclude_doc_ids"] == {"a"}
    assert len(hits) == 1
    assert hits[0].ref_id == "doc-1"


def test_stage_rerank_for_turn_service_uses_injected_stage_function() -> None:
    state = PipelineState(user_input="who am i?")
    observed: dict[str, object] = {}

    def _fake_stage_rerank(pipeline_state, docs_and_scores, **kwargs):
        observed["state"] = pipeline_state
        observed["docs_and_scores"] = docs_and_scores
        observed["kwargs"] = kwargs
        return pipeline_state, [Document(id="doc-2", page_content="winner", metadata={"doc_id": "doc-2"})]

    next_state, hits = context_retrieval_runtime.stage_rerank_for_turn_service(
        state,
        [RetrievalInputRecord(ref_id="doc-1", score=0.8, content="candidate", metadata={"doc_id": "doc-1"})],
        stage_rerank_fn=_fake_stage_rerank,
        utterance="who am i?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=object(),
    )

    assert next_state is state
    assert len(observed["docs_and_scores"]) == 1
    assert observed["kwargs"]["user_doc_id"] == "user-doc"
    assert len(hits) == 1
    assert hits[0].ref_id == "doc-2"


def test_normalize_retrieval_filter_scope_strips_empty_values() -> None:
    scope = context_retrieval_runtime.normalize_retrieval_filter_scope(
        exclude_doc_ids={"", "doc-1"},
        exclude_source_ids={"source-1", ""},
        exclude_turn_scoped_ids={"", "turn-1"},
        segment_ids={"segment-1", ""},
        segment_types={"", "memory"},
    )

    assert scope.exclude_doc_ids == {"doc-1"}
    assert scope.exclude_source_ids == {"source-1"}
    assert scope.exclude_turn_scoped_ids == {"turn-1"}
    assert scope.segment_ids == {"segment-1"}
    assert scope.segment_types == {"memory"}


def test_search_memory_documents_for_retrieval_uses_port_query_when_available() -> None:
    class _Store:
        def __init__(self) -> None:
            self.last_query: MemorySearchQuery | None = None

        def search_memory_records(self, query: MemorySearchQuery):
            self.last_query = query
            return [
                ScoredPortDocument(
                    document=PortDocument(doc_id="doc-1", content="hello", metadata={"doc_id": "doc-1"}),
                    score=0.9,
                )
            ]

    store = _Store()
    scope = context_retrieval_runtime.normalize_retrieval_filter_scope(exclude_doc_ids={"doc-9"})

    docs_and_scores = context_retrieval_runtime.search_memory_documents_for_retrieval(
        store,
        rewritten_query="hello",
        filter_scope=scope,
        k=7,
    )

    assert store.last_query == MemorySearchQuery(query="hello", k=7, exclude_doc_ids={"doc-9"})
    assert len(docs_and_scores) == 1
    assert docs_and_scores[0][0].id == "doc-1"
    assert docs_and_scores[0][1] == 0.9


def test_search_memory_documents_for_retrieval_falls_back_to_similarity_search() -> None:
    class _Store:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def similarity_search_with_score(self, query: str, **kwargs):
            self.calls.append({"query": query, **kwargs})
            return [(Document(id="doc-2", page_content="fallback", metadata={"doc_id": "doc-2"}), 0.4)]

    store = _Store()
    scope = context_retrieval_runtime.normalize_retrieval_filter_scope(exclude_source_ids={"src-1"})

    docs_and_scores = context_retrieval_runtime.search_memory_documents_for_retrieval(
        store,
        rewritten_query="fallback",
        filter_scope=scope,
    )

    assert store.calls == [
        {
            "query": "fallback",
            "k": 18,
            "exclude_doc_ids": set(),
            "exclude_source_ids": {"src-1"},
            "exclude_turn_scoped_ids": set(),
            "segment_ids": set(),
            "segment_types": set(),
        }
    ]
    assert len(docs_and_scores) == 1
    assert docs_and_scores[0][0].id == "doc-2"


def test_resolve_temporal_anaphora_bridge_extracts_anchor_and_elapsed_time_delta() -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    docs_and_scores = [
        (
            Document(
                id="doc-1",
                page_content="candidate",
                metadata={"doc_id": "doc-1", "ts": "2026-03-10T11:30:00+00:00"},
            ),
            0.91,
        )
    ]

    bridge = context_retrieval_runtime.resolve_temporal_anaphora_bridge(
        utterance="how long ago was it?",
        docs_and_scores=docs_and_scores,
        now=now,
    )

    assert bridge["anaphora_detected"] is True
    assert bridge["selected_anchor_doc_id"] == "doc-1"
    assert bridge["target_override_ts"] == "2026-03-10T11:30:00+00:00"
    assert bridge["delta_seconds_raw"] == 1800
    assert bridge["delta_humanized"] == "30 minutes ago"


def test_filter_documents_for_temporal_window_applies_yesterday_window() -> None:
    docs_and_scores = [
        (
            Document(
                id="doc-in",
                page_content="inside window",
                metadata={"doc_id": "doc-in", "ts": "2026-03-09T12:00:00+00:00"},
            ),
            0.8,
        ),
        (
            Document(
                id="doc-out",
                page_content="outside window",
                metadata={"doc_id": "doc-out", "ts": "2026-03-10T12:00:00+00:00"},
            ),
            0.7,
        ),
    ]
    bridge = {
        "window_start": "2026-03-09T00:00:00+00:00",
        "window_end": "2026-03-09T23:59:59.999999+00:00",
    }

    filtered = context_retrieval_runtime.filter_documents_for_temporal_window(
        docs_and_scores=docs_and_scores,
        bridge=bridge,
    )

    assert len(filtered) == 1
    assert filtered[0][0].id == "doc-in"
