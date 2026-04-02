from __future__ import annotations

import arrow
from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot import sat_chatbot_memory_v2 as runtime


def test_stage_rerank_for_turn_service_wrapper_is_retired() -> None:
    assert not hasattr(runtime, "_stage_rerank_for_turn_service")


def test_resolve_context_compat_wrapper_delegates_to_context_service(monkeypatch) -> None:
    observed: dict[str, object] = {}
    expected = {"entities": ["user_name"]}

    def _fake_resolve_context(*args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return expected

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_context", _fake_resolve_context)

    actual = runtime.resolve_context("hello", local_now_iso="2026-03-29T00:00:00+00:00")

    assert actual is expected
    assert observed["args"] == ("hello",)
    assert observed["kwargs"]["local_now_iso"] == "2026-03-29T00:00:00+00:00"


def test_stage_retrieve_compat_smoke_delegates_to_context_service(monkeypatch) -> None:
    observed: dict[str, object] = {}
    expected_state = PipelineState(user_input="q", rewritten_query="q")
    retrieval_hit = runtime.RetrievalInputRecord(
        ref_id="doc-2",
        score=0.75,
        content="hello",
        metadata={"doc_id": "doc-2"},
    )

    def _fake_stage_retrieve_for_turn_service(*args, **kwargs):
        observed["kwargs"] = kwargs
        return expected_state, [retrieval_hit]

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "stage_retrieve_for_turn_service",
        _fake_stage_retrieve_for_turn_service,
    )
    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "document_from_retrieval_input",
        lambda record: Document(id=record.ref_id, page_content=record.content, metadata=record.metadata),
    )

    actual_state, actual_docs_and_scores = runtime.stage_retrieve(store=object(), state=expected_state)

    assert actual_state is expected_state
    assert observed["kwargs"]["retrieval_score_threshold"] == runtime.RETRIEVAL_SCORE_THRESHOLD
    assert [(doc.id, score) for doc, score in actual_docs_and_scores] == [("doc-2", 0.75)]


def test_stage_rerank_compat_smoke_delegates_to_context_service(monkeypatch) -> None:
    observed: dict[str, object] = {}
    state = PipelineState(user_input="who am i?", confidence_decision={})
    input_doc = Document(id="doc-1", page_content="candidate", metadata={"doc_id": "doc-1"})
    input_record = runtime.RetrievalInputRecord(
        ref_id="doc-1",
        score=0.8,
        content="candidate",
        metadata={"doc_id": "doc-1"},
    )
    output_record = runtime.RetrievalInputRecord(
        ref_id="doc-2",
        score=1.0,
        content="winner",
        metadata={"doc_id": "doc-2"},
    )

    class _Clock:
        def now(self):
            return arrow.get("2026-03-10T12:00:00+00:00")

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "retrieval_input_from_document",
        lambda doc, *, score: input_record,
    )

    def _fake_stage_rerank_for_turn_service(*args, **kwargs):
        observed["state"] = args[0]
        observed["kwargs"] = kwargs
        return args[0], [output_record]

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "stage_rerank_for_turn_service",
        _fake_stage_rerank_for_turn_service,
    )
    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "document_from_retrieval_input",
        lambda record: Document(id=record.ref_id, page_content=record.content, metadata=record.metadata),
    )

    next_state, hits = runtime.stage_rerank(
        state,
        [(input_doc, 0.8)],
        utterance="who am i?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=_Clock(),
    )

    assert next_state is state
    assert [doc.id for doc in hits] == ["doc-2"]
    assert observed["kwargs"]["utterance"] == "who am i?"
