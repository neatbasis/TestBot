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


def test_stage_rerank_for_turn_service_wrapper_is_retired() -> None:
    assert not hasattr(runtime, "_stage_rerank_for_turn_service")


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

    def _fake_execute_scorer_contract(request):
        observed["rerank_target"] = request.target.isoformat()
        return runtime.context_retrieval_runtime_service.ScorerExecutionResult(
            rerank_outcome=RerankOutcome(docs=[], scored_candidates=[], ambiguity_detected=False, near_tie_candidates=[])
        )

    def _fake_resolve_target_time(*, utterance, bridge, now):
        observed["resolve_target_time_called"] = True
        return arrow.get("2026-03-10T11:30:00+00:00")

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_temporal_anaphora_bridge", _fake_bridge)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "filter_documents_for_temporal_window", _fake_filter)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_rerank_target_time", _fake_resolve_target_time)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "execute_rerank_scorer_contract", _fake_execute_scorer_contract)

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
    assert observed["resolve_target_time_called"] is True
    assert observed["rerank_target"] == "2026-03-10T11:30:00+00:00"


def test_stage_rerank_uses_runtime_invocation_policy_assembly(monkeypatch) -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="who am i?", confidence_decision={})
    docs_and_scores = [(Document(id="doc-1", page_content="candidate", metadata={"doc_id": "doc-1"}), 0.9)]
    observed: dict[str, object] = {}

    class _Clock:
        def now(self):
            return now

    def _fake_resolve_bridge(*, utterance, docs_and_scores, now):
        return {
            "anaphora_detected": False,
            "anchor_candidates": [],
            "selected_anchor_doc_id": "",
            "selected_anchor_ts": "",
            "target_override_ts": "",
            "delta_seconds_raw": None,
            "delta_humanized": "",
            "time_window": "",
            "window_start": "",
            "window_end": "",
        }

    def _fake_filter(*, docs_and_scores, bridge):
        return docs_and_scores

    def _fake_resolve_target(*, utterance, bridge, now):
        return now

    def _fake_resolve_sigma_seconds(*, now, target, sigma_fraction=0.25, sigma_policy_fn=None):
        observed["sigma_source"] = {
            "now": now,
            "target": target,
            "sigma_fraction": sigma_fraction,
        }
        return 77.0

    def _fake_assemble_policy(*, sigma_seconds, user_doc_id, user_reflection_doc_id, near_tie_delta, top_k=4):
        observed["assembled"] = {
            "sigma_seconds": sigma_seconds,
            "user_doc_id": user_doc_id,
            "user_reflection_doc_id": user_reflection_doc_id,
            "near_tie_delta": near_tie_delta,
            "top_k": top_k,
        }
        return runtime.context_retrieval_runtime_service.RerankInvocationPolicy(
            sigma_seconds=42.0,
            exclude_doc_ids={"assembled-doc"},
            exclude_source_ids={"assembled-source"},
            top_k=7,
            near_tie_delta=0.33,
        )

    def _fake_execute_scorer_contract(request):
        observed["rerank_kwargs"] = {
            "sigma_seconds": request.sigma_seconds,
            "exclude_doc_ids": request.exclude_doc_ids,
            "exclude_source_ids": request.exclude_source_ids,
            "top_k": request.top_k,
            "near_tie_delta": request.near_tie_delta,
        }
        return runtime.context_retrieval_runtime_service.ScorerExecutionResult(
            rerank_outcome=RerankOutcome(docs=[], scored_candidates=[], ambiguity_detected=False, near_tie_candidates=[])
        )

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_temporal_anaphora_bridge", _fake_resolve_bridge)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "filter_documents_for_temporal_window", _fake_filter)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_rerank_target_time", _fake_resolve_target)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_rerank_sigma_seconds", _fake_resolve_sigma_seconds)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "assemble_rerank_invocation_policy", _fake_assemble_policy)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "execute_rerank_scorer_contract", _fake_execute_scorer_contract)

    runtime.stage_rerank(
        state,
        docs_and_scores,
        utterance="who am i?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=_Clock(),
    )

    assert observed["sigma_source"] == {
        "now": now,
        "target": now,
        "sigma_fraction": 0.25,
    }
    assert observed["assembled"] == {
        "sigma_seconds": 77.0,
        "user_doc_id": "user-doc",
        "user_reflection_doc_id": "reflection-doc",
        "near_tie_delta": 0.1,
        "top_k": 4,
    }
    assert observed["rerank_kwargs"]["sigma_seconds"] == 42.0
    assert observed["rerank_kwargs"]["exclude_doc_ids"] == {"assembled-doc"}
    assert observed["rerank_kwargs"]["exclude_source_ids"] == {"assembled-source"}
    assert observed["rerank_kwargs"]["top_k"] == 7
    assert observed["rerank_kwargs"]["near_tie_delta"] == 0.33


def test_stage_rerank_uses_runtime_threshold_profile_policy_assembly(monkeypatch) -> None:
    now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="who am i?", confidence_decision={})
    docs_and_scores = [(Document(id="doc-1", page_content="candidate", metadata={"doc_id": "doc-1"}), 0.9)]
    observed: dict[str, object] = {}

    class _Clock:
        def now(self):
            return now

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "resolve_temporal_anaphora_bridge",
        lambda *, utterance, docs_and_scores, now: {
            "anaphora_detected": False,
            "anchor_candidates": [],
            "selected_anchor_doc_id": "",
            "selected_anchor_ts": "",
            "target_override_ts": "",
            "delta_seconds_raw": None,
            "delta_humanized": "",
            "time_window": "",
            "window_start": "",
            "window_end": "",
        },
    )
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "filter_documents_for_temporal_window", lambda *, docs_and_scores, bridge: docs_and_scores)
    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "resolve_rerank_target_time", lambda *, utterance, bridge, now: now)
    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "assemble_rerank_invocation_policy",
        lambda **kwargs: runtime.context_retrieval_runtime_service.RerankInvocationPolicy(
            sigma_seconds=600.0,
            exclude_doc_ids={"user-doc", "reflection-doc"},
            exclude_source_ids={"user-doc"},
            top_k=4,
            near_tie_delta=0.1,
        ),
    )

    def _fake_threshold_policy(**kwargs):
        observed["threshold_policy_called"] = True
        return runtime.context_retrieval_runtime_service.RerankThresholdProfilePolicy(
            top_final_score_min=0.77,
            min_margin_to_second=0.11,
            allow_ambiguity_override=True,
            ambiguity_override_top_final_score_min=0.93,
        )

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "assemble_rerank_threshold_profile_policy",
        _fake_threshold_policy,
    )
    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "execute_rerank_scorer_contract",
        lambda request: runtime.context_retrieval_runtime_service.ScorerExecutionResult(
            rerank_outcome=RerankOutcome(docs=[], scored_candidates=[], ambiguity_detected=False, near_tie_candidates=[])
        ),
    )

    updated_state, _ = runtime.stage_rerank(
        state,
        docs_and_scores,
        utterance="who am i?",
        user_doc_id="user-doc",
        user_reflection_doc_id="reflection-doc",
        near_tie_delta=0.1,
        clock=_Clock(),
    )

    assert observed["threshold_policy_called"] is True
    assert updated_state.confidence_decision["top_final_score_min"] == 0.77
    assert updated_state.confidence_decision["min_margin_to_second"] == 0.11
    assert updated_state.confidence_decision["allow_ambiguity_override"] is True
    assert updated_state.confidence_decision["ambiguity_override_top_final_score_min"] == 0.93
