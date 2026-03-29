from __future__ import annotations

from langchain_core.documents import Document

from testbot.application.services import context_retrieval_runtime
from testbot.pipeline_state import CandidateFactsArtifact, PipelineState
from testbot.evidence_retrieval import RetrievalInputRecord


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
