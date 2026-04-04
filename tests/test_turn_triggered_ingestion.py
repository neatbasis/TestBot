from collections import deque

from testbot.application.services.turn_service import (
    TurnPipelineDependencies,
    TurnPipelineStageRuntime,
    _ClockSnapshotTimeProvider,
    retrieve_evidence_stage,
)
from testbot.canonical_turn_orchestrator import CanonicalTurnContext
from testbot.logic.turn_pipeline import IntentType
from testbot.pipeline_state import PipelineState
from testbot.source_mode import SourceMode


class _Clock:
    def now(self):
        class _Now:
            def isoformat(self):
                return "2026-04-04T00:00:00+00:00"

        return _Now()


class _ResolvedContext:
    def __init__(self):
        self.history_anchors = ()
        self.ambiguity_flags = ()
        self.continuity_posture = type("ContinuityPosture", (), {"value": "reevaluate"})
        self.prior_intent = None


class _Stabilized:
    def __init__(self):
        self.turn_id = "t1"
        self.utterance_doc_id = "u-doc"
        self.reflection_doc_id = "ref-doc"
        self.dialogue_state_doc_id = "ds-doc"
        self.segment_type = "task"
        self.segment_id = "segment"
        self.segment_membership_edge_refs = []
        self.same_turn_exclusion_doc_ids = []
        self.candidate_facts = []
        self.candidate_speech_acts = []
        self.candidate_dialogue_state = []


def test_turn_triggered_ingestion_starts_for_empty_knowledge_request():
    runtime = {
        "source_turn_triggered_enabled": True,
        "source_mode": SourceMode.BOOTSTRAP_PRELOAD.value,
        "source_ingest_background_in_progress": False,
        "source_ingest_background_request_id": "",
    }
    start_called: dict[str, object] = {}

    def _start_background_source_ingestion(*, runtime: dict[str, object], store, **_kwargs):
        start_called["called"] = True
        runtime["source_ingest_background_in_progress"] = True
        runtime["source_ingest_background_request_id"] = "turn-req"
        return {"started": True, "ingestion_request_id": "turn-req"}

    deps = TurnPipelineDependencies(
        append_session_log=lambda *_a, **_k: None,
        validate_and_log_transition=lambda *_a, **_k: None,
        stage_rewrite_query=lambda _llm, state: state,
        generate_reflection_yaml=lambda *_a, **_k: "",
        intent_classifier_confidence=lambda **_k: 1.0,
        optional_string=lambda _v: None,
        should_force_memory_retrieval_for_identity_recall=lambda **_k: False,
        resolve_context_fn=lambda **_k: _ResolvedContext(),
        intent_telemetry_payload=lambda **_k: {},
        poll_background_source_ingestion=lambda **_k: None,
        start_background_source_ingestion=_start_background_source_ingestion,
        stage_retrieve=lambda store, state, **_k: (state, []),
        stage_rerank=lambda state, *_a, **_k: (state, []),
        selected_decision_from_confidence=lambda *_a, **_k: None,
        minimal_confidence_decision_for_direct_answer=lambda **_k: {},
        resolve_answer_routing_for_stage=lambda state, **_k: (state, None),
        answer_assemble=lambda *_a, **_k: None,
        answer_validate=lambda *_a, **_k: None,
        detect_capability_offer=lambda _text: "",
        ambiguity_score=lambda *_a, **_k: 0.0,
        store_doc_fn=lambda *_a, **_k: None,
        intent_classifier_confidence_threshold=0.5,
    )

    ctx = CanonicalTurnContext(
        state=PipelineState(
            user_input="What is ontology?",
            rewritten_query="What is ontology?",
            resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        ),
        artifacts={
            "turn_id": "t1",
            "resolved_context": _ResolvedContext(),
            "stabilized_turn_state": _Stabilized(),
            "retrieval_requirement": {"requires_retrieval": True, "retrieval_branch": "memory_retrieval"},
            "docs_and_scores": [],
            "hits": [],
            "background_ingestion_in_progress": False,
        },
    )

    stage_runtime = TurnPipelineStageRuntime(
        runtime=runtime,
        llm=object(),
        store=object(),
        utterance="What is ontology?",
        prior_pipeline_state=None,
        prior_continuity=None,
        near_tie_delta=0.1,
        chat_history=deque(),
        capability_status="ask_available",
        capability_snapshot=object(),
        clock=_Clock(),
        io_channel="cli",
        deps=deps,
        snapshot_time_provider=_ClockSnapshotTimeProvider(clock=_Clock()),
    )

    result_ctx = retrieve_evidence_stage(ctx, stage_runtime)

    assert start_called.get("called") is True
    assert result_ctx.artifacts["pending_ingestion_request_id"] == "turn-req"
    assert runtime["source_mode"] == SourceMode.TURN_TRIGGERED_ACQUISITION.value
    assert runtime["source_turn_triggered_supported"] is True
    assert runtime["source_turn_triggered_requests"][0]["utterance"] == "What is ontology?"
