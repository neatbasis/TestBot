from __future__ import annotations

from collections import deque
from dataclasses import replace

import arrow

from testbot.application.services.turn_service import (
    TurnPipelineDependencies,
    TurnPipelineStageRuntime,
    encode_candidates_stage,
    observe_turn_stage,
)
from testbot.canonical_turn_orchestrator import CanonicalTurnContext
from testbot.pipeline_state import PipelineState
from testbot.turn_observation import observe_turn


class _FixedClock:
    def now(self):
        return arrow.get("2026-03-19T00:00:00+00:00")


class _SnapshotProvider:
    def now_iso(self) -> str:
        return "2026-03-19T00:00:00+00:00"


def _deps() -> TurnPipelineDependencies:
    return TurnPipelineDependencies(
        append_session_log=lambda *_args, **_kwargs: None,
        validate_and_log_transition=lambda _check: None,
        stage_rewrite_query=lambda _llm, state: replace(state, rewritten_query="rewritten from fake"),
        generate_reflection_yaml=lambda *_args, **_kwargs: "",
        intent_classifier_confidence=lambda **_kwargs: 0.0,
        optional_string=lambda _value: None,
        should_force_memory_retrieval_for_identity_recall=lambda **_kwargs: False,
        resolve_context_fn=lambda **_kwargs: None,
        intent_telemetry_payload=lambda **_kwargs: {},
        poll_background_source_ingestion=lambda **_kwargs: None,
        start_background_source_ingestion=lambda **_kwargs: {},
        stage_retrieve=lambda *_args, **_kwargs: (_args[1], []),
        stage_rerank=lambda state, *_args, **_kwargs: (state, []),
        selected_decision_from_confidence=lambda *_args, **_kwargs: None,
        minimal_confidence_decision_for_direct_answer=lambda **_kwargs: {},
        resolve_answer_routing_for_stage=lambda state, **_kwargs: (state, None),
        answer_assemble=lambda *_args, **_kwargs: None,
        answer_validate=lambda *_args, **_kwargs: None,
        detect_capability_offer=lambda _text: "",
        ambiguity_score=lambda *_args, **_kwargs: 0.0,
        store_doc_fn=lambda *_args, **_kwargs: None,
        intent_classifier_confidence_threshold=0.5,
    )


def _stage_runtime(*, utterance: str) -> TurnPipelineStageRuntime:
    return TurnPipelineStageRuntime(
        runtime={},
        llm=object(),
        store=object(),
        utterance=utterance,
        prior_pipeline_state=None,
        near_tie_delta=0.05,
        chat_history=deque(),
        capability_status=object(),
        capability_snapshot=object(),
        clock=_FixedClock(),
        io_channel="cli",
        deps=_deps(),
        snapshot_time_provider=_SnapshotProvider(),
    )


def test_observe_turn_stage_can_run_in_isolation() -> None:
    context = CanonicalTurnContext(state=PipelineState(user_input="hello"), artifacts={"turn_id": "turn-1"})

    updated = observe_turn_stage(context, _stage_runtime(utterance="hello"))

    assert updated.state.last_user_message_ts == "2026-03-19T00:00:00+00:00"
    assert updated.artifacts["turn_observation"].utterance == "hello"


def test_encode_candidates_stage_can_run_in_isolation() -> None:
    state = PipelineState(user_input="My name is Ava")
    observation = observe_turn(
        state,
        turn_id="turn-2",
        observed_at="2026-03-19T00:00:00+00:00",
        speaker="user",
        channel="cli",
    )
    context = CanonicalTurnContext(state=state, artifacts={"turn_observation": observation})

    updated = encode_candidates_stage(context, _stage_runtime(utterance="My name is Ava"))

    assert updated.state.rewritten_query == "rewritten from fake"
    assert updated.state.candidate_facts["facts"][0]["key"] == "user_name"
    assert updated.artifacts["encoded_candidates"].rewritten_query == "rewritten from fake"
