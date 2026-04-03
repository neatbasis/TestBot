from __future__ import annotations

from dataclasses import dataclass

import arrow
from langchain_core.documents import Document

from testbot import sat_chatbot_memory_v2 as runtime
from testbot.entrypoints import runtime_turn_pipeline
from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import run_canonical_answer_stage_flow, stage_rerank


@dataclass(frozen=True)
class FakeClock:
    frozen: arrow.Arrow

    def now(self) -> arrow.Arrow:
        return self.frozen


class _DummyResponse:
    def __init__(self, content: str = "") -> None:
        self.content = content


class DummyLLM:
    def invoke(self, _msgs):
        return _DummyResponse("")


def test_stage_rerank_uses_injected_clock_now() -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="what happened")

    updated, _ = stage_rerank(
        state,
        [],
        utterance="what happened",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert updated.confidence_decision["now_ts"] == frozen_now.isoformat()


def test_stage_rerank_delegates_confidence_projection_to_runtime_owner(monkeypatch) -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="what happened")
    observed: dict[str, object] = {}

    def _fake_projection(**kwargs):
        observed.update(kwargs)
        return {"delegated_projection": True, "top_final_score_min": 0.123}

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "project_rerank_confidence_decision", _fake_projection)

    updated, _ = stage_rerank(
        state,
        [],
        utterance="what happened",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert updated.confidence_decision.to_dict() == {"delegated_projection": True, "top_final_score_min": 0.123}
    assert observed["has_context"] is False
    assert observed["sigma_seconds"] > 0


def test_stage_rerank_delegates_scorer_execution_contract_to_runtime_owner(monkeypatch) -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="what happened")
    observed: dict[str, object] = {}
    base_objective_config = runtime.context_retrieval_runtime_service.load_rerank_objective_config()

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "materialize_rerank_scorer_config",
        lambda: runtime.context_retrieval_runtime_service.ScorerExecutionConfig(objective_config=base_objective_config),
    )

    def _fake_normalize_request(**kwargs):
        observed["normalized_kwargs"] = kwargs
        return runtime.context_retrieval_runtime_service.ScorerExecutionRequest(
            docs_and_scores=kwargs["docs_and_scores"],
            now=kwargs["now"],
            target=kwargs["target"],
            sigma_seconds=kwargs["invocation_policy"].sigma_seconds,
            exclude_doc_ids=kwargs["invocation_policy"].exclude_doc_ids,
            exclude_source_ids=kwargs["invocation_policy"].exclude_source_ids,
            top_k=kwargs["invocation_policy"].top_k,
            near_tie_delta=kwargs["invocation_policy"].near_tie_delta,
            scorer_config=kwargs["scorer_config"].objective_config,
        )

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "normalize_scorer_execution_request", _fake_normalize_request)

    def _fake_execute(request):
        observed["request"] = request
        doc = Document(id="doc-1", page_content="winner", metadata={"doc_id": "doc-1", "ts": "2026-03-10T11:30:00+00:00"})
        outcome = runtime.context_retrieval_runtime_service.RerankOutcome(
            docs=[doc],
            ambiguity_detected=False,
            near_tie_candidates=[],
            scored_candidates=[{"doc_id": "doc-1", "final_score": 0.9}],
        )
        return runtime.context_retrieval_runtime_service.ScorerExecutionResult(rerank_outcome=outcome)

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "execute_rerank_scorer_contract", _fake_execute)

    updated, hits = stage_rerank(
        state,
        [],
        utterance="what happened",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    request = observed["request"]
    assert isinstance(request, runtime.context_retrieval_runtime_service.ScorerExecutionRequest)
    assert observed["normalized_kwargs"]["scorer_config"].objective_config is base_objective_config
    assert request.top_k == 4
    assert request.exclude_doc_ids == {"u1", "r1"}
    assert request.exclude_source_ids == {"u1"}
    assert request.scorer_config is base_objective_config
    assert len(hits) == 1
    assert updated.reranked_hits[0].doc_id == "doc-1"


def test_stage_rerank_delegates_scorer_result_interpretation_to_runtime_owner(monkeypatch) -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="what happened")
    observed: dict[str, object] = {}

    doc = Document(id="doc-1", page_content="winner", metadata={"doc_id": "doc-1", "ts": "2026-03-10T11:30:00+00:00"})
    outcome = runtime.context_retrieval_runtime_service.RerankOutcome(
        docs=[doc],
        ambiguity_detected=False,
        near_tie_candidates=[],
        scored_candidates=[{"doc_id": "doc-1", "final_score": 0.9}],
    )
    scorer_result = runtime.context_retrieval_runtime_service.ScorerExecutionResult(rerank_outcome=outcome)

    monkeypatch.setattr(
        runtime.context_retrieval_runtime_service,
        "execute_rerank_scorer_contract",
        lambda request: scorer_result,
    )

    def _fake_interpret(result):
        observed["result"] = result
        return runtime.context_retrieval_runtime_service.ScorerInterpretationResult(
            hits=[doc],
            has_context=True,
        )

    monkeypatch.setattr(runtime.context_retrieval_runtime_service, "interpret_rerank_scorer_result", _fake_interpret)

    updated, hits = stage_rerank(
        state,
        [],
        utterance="what happened",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert observed["result"] is scorer_result
    assert [h.doc_id for h in updated.reranked_hits] == ["doc-1"]
    assert [d.id for d in hits] == ["doc-1"]


def test_run_canonical_answer_stage_flow_time_query_ignores_seeded_same_turn_and_synthetic_hits(monkeypatch) -> None:
    captured_doc_ids: list[str] = []

    def _stub_pipeline(**kwargs):
        docs_and_scores = kwargs["store"].similarity_search_with_score(
            "q",
            k=18,
            exclude_doc_ids={"time-turn-doc"},
            exclude_source_ids={"time-turn-doc"},
            exclude_turn_scoped_ids={"time-turn-doc"},
        )
        captured_doc_ids.extend(str(doc.id or "") for doc, _score in docs_and_scores)
        return kwargs["state"], []

    monkeypatch.setattr(runtime_turn_pipeline, "run_runtime_turn_pipeline", _stub_pipeline)
    frozen_now = arrow.get("2026-03-10T22:30:00+00:00")
    state = PipelineState(user_input="what is tomorrow?", last_user_message_ts="2026-03-10T22:00:00+00:00")
    hits = [
        Document(
            id="time-turn-doc",
            page_content="same-turn note",
            metadata={"doc_id": "time-turn-doc", "turn_doc_id": "time-turn-doc"},
        ),
        Document(
            id="time-seeded-artifact",
            page_content="serialized stage payload",
            metadata={"doc_id": "time-seeded-artifact", "pipeline_state_snapshot": True},
        ),
    ]

    _ = run_canonical_answer_stage_flow(
        DummyLLM(),
        state,
        chat_history=[],
        hits=hits,
        capability_status="ask_unavailable",
        clock=FakeClock(frozen_now),
        timezone="Europe/Helsinki",
    )

    assert captured_doc_ids == []


def test_stage_rerank_pronoun_elapsed_time_emits_anchor_and_delta() -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="How long ago was it?")
    docs_and_scores = [
        (
            Document(
                id="mem-1",
                page_content="You mentioned it before",
                metadata={"doc_id": "mem-1", "type": "user_utterance", "ts": "2026-03-10T11:30:00+00:00"},
            ),
            0.82,
        )
    ]

    updated, hits = stage_rerank(
        state,
        docs_and_scores,
        utterance="How long ago was it?",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert hits
    assert updated.confidence_decision["anaphora_detected"] is True
    assert updated.confidence_decision["selected_anchor_doc_id"] == "mem-1"
    assert updated.confidence_decision["selected_anchor_ts"] == "2026-03-10T11:30:00+00:00"
    assert updated.confidence_decision["computed_delta_raw_seconds"] == 1800
    assert updated.confidence_decision["computed_delta_humanized"] == "30 minutes ago"


def test_stage_rerank_yesterday_window_filters_candidates() -> None:
    frozen_now = arrow.get("2026-03-10T12:00:00+00:00")
    state = PipelineState(user_input="What happened yesterday?")
    docs_and_scores = [
        (
            Document(
                id="yesterday-doc",
                page_content="Yesterday note",
                metadata={"doc_id": "yesterday-doc", "type": "user_utterance", "ts": "2026-03-09T08:00:00+00:00"},
            ),
            0.70,
        ),
        (
            Document(
                id="today-doc",
                page_content="Today note",
                metadata={"doc_id": "today-doc", "type": "user_utterance", "ts": "2026-03-10T08:00:00+00:00"},
            ),
            0.95,
        ),
    ]

    updated, hits = stage_rerank(
        state,
        docs_and_scores,
        utterance="What happened yesterday?",
        user_doc_id="u1",
        user_reflection_doc_id="r1",
        near_tie_delta=0.02,
        clock=FakeClock(frozen_now),
    )

    assert [doc.id for doc in hits] == ["yesterday-doc"]
    assert updated.confidence_decision["time_window"] == "yesterday"
    assert updated.confidence_decision["window_start"].startswith("2026-03-09T00:00:00")
