from __future__ import annotations

from collections import deque

from testbot.continuity_read_model import CommittedTurnContinuity, ContinuityReadModel
from testbot.entrypoints import runtime_turn_pipeline
from testbot.pipeline_state import PipelineState


def _hooks() -> runtime_turn_pipeline.RuntimeTurnPipelineHooks:
    return runtime_turn_pipeline.RuntimeTurnPipelineHooks(
        append_session_log=lambda *_a, **_k: None,
        validate_and_log_transition=lambda *_a, **_k: None,
        stage_rewrite_query=lambda *_a, **_k: None,
        generate_reflection_yaml=lambda *_a, **_k: "",
        intent_classifier_confidence=lambda **_k: 0.0,
        optional_string=lambda _v: None,
        should_force_memory_retrieval_for_identity_recall=lambda **_k: False,
        resolve_context_fn=lambda **_k: None,
        intent_telemetry_payload=lambda **_k: {},
        poll_background_source_ingestion=lambda **_k: None,
        start_background_source_ingestion=lambda **_k: {},
        stage_retrieve=lambda *_a, **_k: None,
        stage_rerank=lambda *_a, **_k: None,
        selected_decision_from_confidence=lambda *_a, **_k: None,
        minimal_confidence_decision_for_direct_answer=lambda **_k: {},
        resolve_answer_routing_for_stage=lambda *_a, **_k: None,
        answer_assemble=lambda *_a, **_k: None,
        answer_validate=lambda *_a, **_k: None,
        detect_capability_offer=lambda _text: "",
        ambiguity_score=lambda *_a, **_k: 0.0,
        store_doc_fn=lambda *_a, **_k: None,
        intent_classifier_confidence_threshold=0.5,
        document_from_retrieval_input=lambda record: record,
    )


def test_run_runtime_turn_pipeline_threads_explicit_prior_continuity_to_canonical_turn_runtime(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _stub(**kwargs):
        captured.update(kwargs)
        return PipelineState(user_input="done"), []

    monkeypatch.setattr(runtime_turn_pipeline, "run_canonical_turn_pipeline", _stub)

    prior_continuity = ContinuityReadModel(
        committed_turn=CommittedTurnContinuity(
            turn_id="prior-turn",
            commit_stage="answer.commit",
            pending_ingestion_request_id="ingest-42",
        )
    )

    runtime_turn_pipeline.run_runtime_turn_pipeline(
        runtime={},
        llm=object(),
        store=object(),
        state=PipelineState(user_input="hello"),
        utterance="hello",
        prior_pipeline_state=PipelineState(user_input="prior"),
        prior_continuity=prior_continuity,
        turn_id="turn-1",
        near_tie_delta=0.05,
        chat_history=deque(),
        capability_status=object(),
        capability_snapshot=object(),
        clock=object(),
        hooks=_hooks(),
    )

    assert captured["prior_continuity"] is prior_continuity
