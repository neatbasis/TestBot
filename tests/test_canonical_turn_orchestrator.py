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
            if name == "context.resolve":
                ctx.artifacts["resolved_context"] = {"continuity_posture": "reevaluate"}
            if name == "intent.resolve":
                assert ctx.artifacts.get("stabilized_turn_state") is not None
                assert ctx.state.same_turn_exclusion.get("excluded_doc_ids") == ["turn-1", "ref-1"]
                assert ctx.artifacts.get("resolved_context") == {"continuity_posture": "reevaluate"}
                ctx.state = replace(ctx.state, resolved_intent="memory_recall")
            if name == "retrieve.evidence":
                ctx.artifacts["retrieval_result"] = {"posture": "empty_evidence"}
            if name == "answer.assemble":
                ctx.artifacts["answer_assembly_contract"] = {"decision_class": "answer_from_memory"}
            if name == "answer.validate":
                ctx.artifacts["answer_validation_contract"] = type("Validation", (), {"passed": True})()
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
            if name == "observe.turn":
                ctx.artifacts["turn_observation"] = {"turn_id": "turn-1", "utterance": "hello"}
            if name == "encode.candidates":
                ctx.artifacts["encoded_candidates"] = {"facts": []}
            if name == "stabilize.pre_route":
                assert ctx.artifacts.get("policy_decision") is None
                ctx.artifacts["stabilized_turn_state"] = {"turn_id": "turn-1"}
            if name == "context.resolve":
                ctx.artifacts["resolved_context"] = {"continuity_posture": "reevaluate"}
            if name == "intent.resolve":
                assert ctx.artifacts.get("stabilized_turn_state") == {"turn_id": "turn-1"}
                assert ctx.artifacts.get("policy_decision") is None
                assert ctx.artifacts.get("resolved_context") == {"continuity_posture": "reevaluate"}
                ctx.artifacts["retrieval_requirement"] = {"requires_retrieval": False, "reason": "non_memory_intent"}
            if name == "retrieve.evidence":
                assert ctx.artifacts.get("policy_decision") is None
                assert ctx.artifacts.get("retrieval_requirement") == {
                    "requires_retrieval": False,
                    "reason": "non_memory_intent",
                }
                ctx.artifacts["retrieval_result"] = {"posture": "not_requested"}
            if name == "policy.decide":
                assert ctx.artifacts.get("policy_decision") is None
                ctx.artifacts["policy_decision"] = {"retrieval_branch": "direct_answer"}
            if name == "answer.assemble":
                ctx.artifacts["answer_assembly_contract"] = {"decision_class": "answer_from_memory"}
            if name == "answer.validate":
                ctx.artifacts["answer_validation_contract"] = type("Validation", (), {"passed": True})()
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


def test_intent_stage_consumes_stabilized_and_context_artifacts_not_raw_input() -> None:
    state = PipelineState(user_input="RAW_INPUT_SHOULD_NOT_ROUTE")
    context = CanonicalTurnContext(state=state)

    stages: list[CanonicalStage] = []
    for stage_name in CanonicalTurnOrchestrator.STAGE_ORDER:

        def _handler(ctx: CanonicalTurnContext, name: str = stage_name) -> CanonicalTurnContext:
            if name == "observe.turn":
                ctx.artifacts["turn_observation"] = {"turn_id": "turn-1", "utterance": "what is ontology?"}
            if name == "encode.candidates":
                ctx.artifacts["encoded_candidates"] = {"facts": [{"key": "utterance_raw", "value": "what is ontology?"}]}
            if name == "stabilize.pre_route":
                ctx.artifacts["stabilized_turn_state"] = {"candidate_facts": [{"key": "utterance_raw", "value": "what is ontology?"}]}
            if name == "context.resolve":
                ctx.artifacts["resolved_context"] = {"continuity_posture": "reevaluate"}
            if name == "intent.resolve":
                assert ctx.artifacts["stabilized_turn_state"]["candidate_facts"][0]["value"] == "what is ontology?"
                assert ctx.artifacts["resolved_context"]["continuity_posture"] == "reevaluate"
                assert ctx.state.user_input == "RAW_INPUT_SHOULD_NOT_ROUTE"
                ctx.state = replace(ctx.state, classified_intent="knowledge_question", resolved_intent="knowledge_question")
            if name == "retrieve.evidence":
                ctx.artifacts["retrieval_result"] = {"posture": "empty_evidence"}
            if name == "answer.assemble":
                ctx.artifacts["answer_assembly_contract"] = {"decision_class": "answer_from_memory"}
            if name == "answer.validate":
                ctx.artifacts["answer_validation_contract"] = type("Validation", (), {"passed": True})()
            return ctx

        stages.append(CanonicalStage(name=stage_name, handler=_handler))

    final_context = CanonicalTurnOrchestrator(stages=stages).run(context)

    assert final_context.state.resolved_intent == "knowledge_question"


def test_orchestrator_rejects_intent_resolution_without_stabilization_artifacts() -> None:
    state = PipelineState(user_input="Hi! I'm Sebastian")
    context = CanonicalTurnContext(state=state)

    stages = [_make_stage(name) for name in CanonicalTurnOrchestrator.STAGE_ORDER]
    orchestrator = CanonicalTurnOrchestrator(stages=stages)

    with pytest.raises(RuntimeError, match="stabilize.pre_route must produce stabilized_turn_state artifact"):
        orchestrator.run(context)
