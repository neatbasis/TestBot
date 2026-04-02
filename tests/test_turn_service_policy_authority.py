from __future__ import annotations

from testbot.application.services import turn_service
from testbot.canonical_turn_orchestrator import CanonicalTurnContext
from testbot.evidence_retrieval import EvidenceBundle, retrieval_result
from testbot.intent_router import IntentType
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionClass, DecisionObject


class _Clock:
    def now(self):
        class _Now:
            def isoformat(self) -> str:
                return "2026-04-02T00:00:00+00:00"

        return _Now()


class _Snapshot:
    runtime_capability_status = None


def test_policy_decide_stage_ignores_confidence_payload_override_in_canonical_path(monkeypatch) -> None:
    sentinel_decision = DecisionObject(
        decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
        retrieval_branch="direct_answer",
        rationale="explicit policy-stage authority",
        reasoning={"authority_stage": "policy", "authority_source": "decide_from_evidence"},
    )

    def _selected_decision_from_confidence(*_args, **_kwargs):
        raise AssertionError("canonical policy_decide_stage must not recover decision authority from confidence_decision")

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
        selected_decision_from_confidence=_selected_decision_from_confidence,
        minimal_confidence_decision_for_direct_answer=lambda **_k: {},
        resolve_answer_routing_for_stage=lambda state, **_k: (state, None),
        answer_assemble=lambda *_a, **_k: None,
        answer_validate=lambda *_a, **_k: None,
        detect_capability_offer=lambda _text: "",
        ambiguity_score=lambda *_a, **_k: 0.0,
        store_doc_fn=lambda *_a, **_k: None,
        intent_classifier_confidence_threshold=0.5,
    )

    runtime = turn_service.TurnPipelineStageRuntime(
        runtime={},
        llm=object(),
        store=object(),
        utterance="what time is it?",
        prior_pipeline_state=None,
        prior_continuity=None,
        near_tie_delta=0.05,
        chat_history=[],
        capability_status="ask_unavailable",
        capability_snapshot=_Snapshot(),
        clock=_Clock(),
        io_channel="cli",
        deps=deps,
        snapshot_time_provider=turn_service._ClockSnapshotTimeProvider(clock=_Clock()),
    )
    context = CanonicalTurnContext(
        state=PipelineState(
            user_input="what time is it?",
            resolved_intent=IntentType.TIME_QUERY.value,
            confidence_decision={
                "allow_selected_decision_override": True,
                "selected_decision_authority_stage": "policy",
                "selected_decision_object": {
                    "decision_class": DecisionClass.ANSWER_FROM_MEMORY.value,
                    "retrieval_branch": "memory_retrieval",
                },
            },
        ),
        artifacts={
            "retrieval_requirement": {
                "requires_retrieval": False,
                "reason": "time_query_routes_direct",
                "retrieval_branch": "direct_answer",
            },
            "retrieval_result": retrieval_result(
                evidence_bundle=EvidenceBundle(),
                retrieval_candidates_considered=0,
                hit_count=0,
            ),
            "guard_forced_memory_retrieval": False,
        },
    )

    monkeypatch.setattr(turn_service, "decide_from_evidence", lambda **_kwargs: sentinel_decision)

    updated = turn_service.policy_decide_stage(context, runtime)

    assert updated.artifacts["decision_object"] is sentinel_decision
