from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

from testbot.application.services import turn_service
from testbot.pipeline_state import PipelineState


class _Clock:
    def now(self):
        class _Now:
            def isoformat(self):
                return "2026-03-19T00:00:00+00:00"

        return _Now()


class _Snapshot:
    runtime_capability_status = None


def test_run_canonical_turn_pipeline_service_preserves_canonical_stage_order(monkeypatch):
    order: list[str] = []

    def _mk(name: str):
        def _stage(ctx, _runtime):
            order.append(name)
            ctx.artifacts.setdefault("hits", [])
            if name == "observe.turn":
                ctx.artifacts["turn_observation"] = object()
            elif name == "encode.candidates":
                ctx.artifacts["encoded_candidates"] = object()
            elif name == "stabilize.pre_route":
                ctx.artifacts["stabilized_turn_state"] = {"turn_id": "t-1"}
            elif name == "context.resolve":
                ctx.artifacts["resolved_context"] = {"history_anchors": []}
            elif name == "retrieve.evidence":
                ctx.artifacts["retrieval_result"] = {"posture": "empty_evidence", "retrieval_candidates_considered": 0, "hit_count": 0}
            elif name == "answer.assemble":
                ctx.artifacts["answer_assembly_contract"] = {"decision": "ok"}
            elif name == "answer.validate":
                ctx.artifacts["answer_validation_contract"] = {"passed": True}
            elif name == "answer.render":
                ctx.artifacts["answer_render_contract"] = {"text": "ok"}
            return ctx

        return _stage

    monkeypatch.setattr(turn_service, "observe_turn_stage", _mk("observe.turn"))
    monkeypatch.setattr(turn_service, "encode_candidates_stage", _mk("encode.candidates"))
    monkeypatch.setattr(turn_service, "stabilize_pre_route_stage", _mk("stabilize.pre_route"))
    monkeypatch.setattr(turn_service, "context_resolve_stage", _mk("context.resolve"))
    monkeypatch.setattr(turn_service, "intent_resolve_stage", _mk("intent.resolve"))
    monkeypatch.setattr(turn_service, "retrieve_evidence_stage", _mk("retrieve.evidence"))
    monkeypatch.setattr(turn_service, "policy_decide_stage", _mk("policy.decide"))
    monkeypatch.setattr(turn_service, "answer_assemble_stage", _mk("answer.assemble"))
    monkeypatch.setattr(turn_service, "answer_validate_stage", _mk("answer.validate"))
    monkeypatch.setattr(turn_service, "answer_render_stage", _mk("answer.render"))

    def _commit_stage(ctx, _runtime):
        order.append("answer.commit")
        ctx.artifacts["hits"] = [Document(page_content="committed", metadata={"doc_id": "d1"})]
        return ctx

    monkeypatch.setattr(turn_service, "answer_commit_stage", _commit_stage)

    deps = turn_service.TurnPipelineDependencies(
        append_session_log=lambda *_a, **_k: None,
        validate_and_log_transition=lambda *_a, **_k: None,
        stage_rewrite_query=lambda _llm, state: state,
        generate_reflection_yaml=lambda *_a, **_k: "",
        intent_classifier_confidence=lambda **_k: 0.0,
        optional_string=lambda _v: None,
        should_force_memory_retrieval_for_identity_recall=lambda **_k: False,
        resolve_context_fn=lambda **_k: None,
        intent_telemetry_payload=lambda **_k: {},
        poll_background_source_ingestion=lambda **_k: None,
        start_background_source_ingestion=lambda **_k: {},
        stage_retrieve=lambda *_a, **_k: (_a[1], []),
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

    final_state, hits = turn_service.run_canonical_turn_pipeline_service(
        runtime={},
        llm=object(),
        store=object(),
        state=PipelineState(user_input="hello", confidence_decision={}),
        utterance="hello",
        prior_pipeline_state=None,
        turn_id="t-1",
        near_tie_delta=0.05,
        chat_history=deque(),
        capability_status="ask_unavailable",
        capability_snapshot=_Snapshot(),
        clock=_Clock(),
        io_channel="cli",
        deps=deps,
    )

    assert order == list(turn_service.CANONICAL_STAGE_SEQUENCE)
    assert final_state.confidence_decision["stage_audit_trail"] == list(turn_service.CANONICAL_STAGE_SEQUENCE)
    assert len(hits) == 1
    assert hits[0].metadata["doc_id"] == "d1"
