from __future__ import annotations

import arrow
from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.rerank import RerankOutcome
from testbot import sat_chatbot_memory_v2 as runtime


def test_should_force_memory_retrieval_wrapper_delegates_to_context_retrieval_runtime(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def _fake_should_force(**kwargs):
        observed.update(kwargs)
        return True

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "should_force_memory_retrieval_for_identity_recall",
        _fake_should_force,
    )

    result = runtime._should_force_memory_retrieval_for_identity_recall(
        utterance="who am i?",
        prior_state=PipelineState(user_input="my name is sam"),
        continuity_evidence=("commit.confirmed_user_facts:user_name",),
        context_history_anchors=(),
    )

    assert result is True
    assert observed["utterance"] == "who am i?"


def test_resolve_context_wrapper_delegates_to_context_retrieval_runtime(monkeypatch) -> None:
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
    assert observed["kwargs"]["resolve_context_fn"] is runtime._resolve_context_from_domain


def test_stage_retrieve_for_turn_service_wrapper_delegates_to_context_retrieval_runtime(monkeypatch) -> None:
    observed: dict[str, object] = {}
    expected_state = PipelineState(user_input="q")
    expected_hit = runtime.RetrievalInputRecord(ref_id="doc-1", score=0.5, content="hello", metadata={"doc_id": "doc-1"})

    def _fake_stage_retrieve_for_turn_service(*args, **kwargs):
        observed.update(kwargs)
        return expected_state, [expected_hit]

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "stage_retrieve_for_turn_service",
        _fake_stage_retrieve_for_turn_service,
    )

    actual_state, actual_hits = runtime._stage_retrieve_for_turn_service(store=object(), state=expected_state)

    assert actual_state is expected_state
    assert actual_hits == [expected_hit]
    assert observed["stage_retrieve_fn"] is runtime.stage_retrieve


def test_stage_rerank_for_turn_service_wrapper_delegates_to_context_retrieval_runtime(monkeypatch) -> None:
    observed: dict[str, object] = {}
    expected_state = PipelineState(user_input="q")
    retrieval_hit = runtime.RetrievalInputRecord(ref_id="doc-1", score=1.0, content="x", metadata={"doc_id": "doc-1"})

    def _fake_stage_rerank_for_turn_service(*args, **kwargs):
        observed.update(kwargs)
        return expected_state, [retrieval_hit]

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "stage_rerank_for_turn_service",
        _fake_stage_rerank_for_turn_service,
    )

    actual_state, actual_hits = runtime._stage_rerank_for_turn_service(
        state=expected_state,
        retrieval_candidates=[retrieval_hit],
        utterance="who am i?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=runtime.SystemClock(),
    )

    assert actual_state is expected_state
    assert actual_hits == [retrieval_hit]
    assert observed["stage_rerank_fn"] is runtime.stage_rerank


def test_document_conversion_wrappers_delegate_to_context_retrieval_runtime(monkeypatch) -> None:
    observed: dict[str, object] = {}
    expected_doc = Document(id="doc-1", page_content="hello", metadata={"doc_id": "doc-1"})
    expected_record = runtime.RetrievalInputRecord(ref_id="doc-1", score=0.8, content="hello", metadata={"doc_id": "doc-1"})

    def _fake_to_record(doc: Document, *, score: float):
        observed["to_record"] = (doc, score)
        return expected_record

    def _fake_to_doc(record):
        observed["to_doc"] = record
        return expected_doc

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "retrieval_input_from_document", _fake_to_record)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "document_from_retrieval_input", _fake_to_doc)

    assert runtime._retrieval_input_from_document(expected_doc, score=0.8) is expected_record
    assert runtime._document_from_retrieval_input(expected_record) is expected_doc
    assert observed["to_record"][1] == 0.8
    assert observed["to_doc"] is expected_record


def test_stage_rerank_uses_runtime_temporal_bridge_helpers(monkeypatch) -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    observed: dict[str, object] = {}
    state = PipelineState(user_input="how long ago was it?", confidence_decision={})
    docs_and_scores = [
        (Document(id="doc-1", page_content="candidate", metadata={"doc_id": "doc-1", "ts": "2026-03-10T11:30:00+00:00"}), 0.9)
    ]

    class _Clock:
        def now(self):
            return now

    def _fake_bridge(*, utterance, docs_and_scores, now):
        observed["bridge_called"] = True
        return {
            "anaphora_detected": True,
            "anchor_candidates": [{"doc_id": "doc-1", "ts": "2026-03-10T11:30:00+00:00", "confidence": 0.9}],
            "selected_anchor_doc_id": "doc-1",
            "selected_anchor_ts": "2026-03-10T11:30:00+00:00",
            "target_override_ts": "2026-03-10T11:30:00+00:00",
            "delta_seconds_raw": 1800,
            "delta_humanized": "30 minutes ago",
            "time_window": "",
            "window_start": "",
            "window_end": "",
        }

    def _fake_filter(*, docs_and_scores, bridge):
        observed["filter_called"] = True
        return docs_and_scores

    def _fake_rerank(*args, **kwargs):
        observed["rerank_target"] = kwargs["target"].isoformat()
        return RerankOutcome(docs=[], scored_candidates=[], ambiguity_detected=False, near_tie_candidates=[])

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_temporal_anaphora_bridge", _fake_bridge)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "filter_documents_for_temporal_window", _fake_filter)
    monkeypatch.setattr(runtime, "rerank_docs_with_time_and_type_outcome", _fake_rerank)

    runtime.stage_rerank(
        state,
        docs_and_scores,
        utterance="how long ago was it?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=_Clock(),
    )

    assert observed["bridge_called"] is True
    assert observed["filter_called"] is True
    assert observed["rerank_target"] == "2026-03-10T11:30:00+00:00"
