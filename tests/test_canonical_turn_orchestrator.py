from __future__ import annotations

from dataclasses import replace

import pytest

from testbot.candidate_encoding import encode_turn_candidates
from testbot.canonical_turn_orchestrator import CanonicalStage, CanonicalTurnContext, CanonicalTurnOrchestrator
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionClass, DecisionObject
from testbot.sat_chatbot_memory_v2 import _answer_routing_from_decision_object
from testbot.turn_observation import observe_turn


def _make_stage(name: str):
    def _handler(context: CanonicalTurnContext) -> CanonicalTurnContext:
        return context

    return CanonicalStage(name=name, handler=_handler)


def test_orchestrator_rejects_missing_or_reordered_stages() -> None:
    truncated = [
        _make_stage("observe.turn"),
        _make_stage("encode.candidates"),
    ]
    with pytest.raises(ValueError):
        CanonicalTurnOrchestrator(stages=truncated)

    reordered = [
        _make_stage("observe.turn"),
        _make_stage("context.resolve"),
        *[_make_stage(name) for name in CanonicalTurnOrchestrator.STAGE_ORDER[2:]],
    ]
    with pytest.raises(ValueError):
        CanonicalTurnOrchestrator(stages=reordered)


def test_orchestrator_executes_all_11_canonical_stages_in_order() -> None:
    state = PipelineState(user_input="hello")
    context = CanonicalTurnContext(state=state)

    stages: list[CanonicalStage] = []
    for stage_name in CanonicalTurnOrchestrator.STAGE_ORDER:

        def _handler(ctx: CanonicalTurnContext, name: str = stage_name) -> CanonicalTurnContext:
            if name == "observe.turn":
                ctx.artifacts["turn_observation"] = observe_turn(
                    ctx.state,
                    turn_id="turn-1",
                    observed_at="2026-03-07T10:00:00+00:00",
                    speaker="user",
                    channel="cli",
                )
            if name == "encode.candidates":
                assert "turn_observation" in ctx.artifacts
                encoded = encode_turn_candidates(
                    ctx.state,
                    observation=ctx.artifacts["turn_observation"],
                    rewritten_query=ctx.state.user_input,
                )
                ctx.artifacts["encoded_candidates"] = encoded
            if name == "stabilize.pre_route":
                assert "encoded_candidates" in ctx.artifacts
                ctx.artifacts["stabilized_turn_state"] = {
                    "same_turn_exclusion_doc_ids": ["turn-1", "ref-1"],
                    "candidate_facts": ctx.artifacts["encoded_candidates"].as_artifact_payload()["facts"],
                }
                ctx.state = replace(
                    ctx.state,
                    same_turn_exclusion={
                        "excluded_doc_ids": ["turn-1", "ref-1"],
                        "reason": "stabilize.pre_route",
                    },
                )
            if name == "intent.resolve":
                assert ctx.artifacts.get("stabilized_turn_state") is not None
                assert ctx.state.same_turn_exclusion.get("excluded_doc_ids") == ["turn-1", "ref-1"]
                ctx.state = replace(ctx.state, resolved_intent="memory_recall")
            if name == "retrieve.evidence":
                ctx.artifacts["retrieval_result"] = {"posture": "empty_evidence"}
            return ctx

        stages.append(CanonicalStage(name=stage_name, handler=_handler))

    orchestrator = CanonicalTurnOrchestrator(stages=stages)
    final_context = orchestrator.run(context)

    assert final_context.stage_audit_trail == list(CanonicalTurnOrchestrator.STAGE_ORDER)
    assert final_context.state.resolved_intent == "memory_recall"




def test_orchestrator_stabilizes_before_route_authority_assignment() -> None:
    state = PipelineState(user_input="hello")
    context = CanonicalTurnContext(state=state, artifacts={"policy_decision": None})

    stages: list[CanonicalStage] = []
    for stage_name in CanonicalTurnOrchestrator.STAGE_ORDER:

        def _handler(ctx: CanonicalTurnContext, name: str = stage_name) -> CanonicalTurnContext:
            if name == "stabilize.pre_route":
                assert ctx.artifacts.get("policy_decision") is None
                ctx.artifacts["stabilized_turn_state"] = {"turn_id": "turn-1"}
            if name == "intent.resolve":
                assert ctx.artifacts.get("stabilized_turn_state") == {"turn_id": "turn-1"}
                assert ctx.artifacts.get("policy_decision") is None
                ctx.artifacts["policy_decision"] = {"retrieval_branch": "direct_answer"}
            if name == "retrieve.evidence":
                assert ctx.artifacts.get("policy_decision") == {"retrieval_branch": "direct_answer"}
                ctx.artifacts["retrieval_result"] = {"posture": "not_requested"}
            return ctx

        stages.append(CanonicalStage(name=stage_name, handler=_handler))

    orchestrator = CanonicalTurnOrchestrator(stages=stages)
    final_context = orchestrator.run(context)

    assert final_context.artifacts["policy_decision"] == {"retrieval_branch": "direct_answer"}

def test_encode_turn_candidates_extracts_name_fact_for_stabilization() -> None:
    state = PipelineState(user_input="My name is Sebastian")
    observation = observe_turn(
        state,
        turn_id="turn-identity",
        observed_at="2026-03-07T10:00:00+00:00",
        speaker="user",
        channel="cli",
    )

    encoded = encode_turn_candidates(state, observation=observation, rewritten_query="my name is sebastian")

    assert any(fact.key == "user_name" and fact.value == "Sebastian" for fact in encoded.facts)
    assert encoded.dialogue_state and encoded.dialogue_state[0].label == "self_identification"


def test_canonical_answer_from_memory_decision_maps_to_memory_grounded_route() -> None:
    decision = DecisionObject(
        decision_class=DecisionClass.ANSWER_FROM_MEMORY,
        retrieval_branch="memory_retrieval",
        rationale="confident evidence bundle supports memory-grounded answer",
        reasoning={"evidence_posture": "scored_non_empty"},
    )

    routing = _answer_routing_from_decision_object(decision, capability_status="ask_unavailable")

    assert routing.fallback_action == "ANSWER_FROM_MEMORY"
    assert routing.canonical_response_token == "LLM_DRAFT"
    assert routing.rationale["decision_class"] == "answer_from_memory"
