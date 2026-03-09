from __future__ import annotations

from dataclasses import replace

import pytest

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_rendering import render_answer
from testbot.answer_validation import validate_answer_assembly_boundary
from testbot.canonical_turn_orchestrator import CanonicalStage, CanonicalTurnContext, CanonicalTurnOrchestrator
from testbot.context_resolution import ContinuityPosture, ResolvedContext
from testbot.pipeline_state import PipelineState


def test_canonical_pipeline_semantic_contracts_require_cross_stage_dependencies() -> None:
    state = PipelineState(user_input="Who am I?")
    context = CanonicalTurnContext(state=state)

    def _observe_turn(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["turn_observation"] = {"turn_id": "turn-1", "utterance": "Who am I?"}
        return ctx

    def _encode_candidates(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["encoded_candidates"] = {
            "facts": [{"key": "utterance_raw", "value": "Who am I?"}],
            "rewritten_query": "who am i",
        }
        return ctx

    def _stabilize_pre_route(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        utterance = ctx.artifacts["encoded_candidates"]["facts"][0]["value"]
        ctx.artifacts["stabilized_turn_state"] = {
            "candidate_facts": [{"key": "utterance_raw", "value": utterance}],
            "same_turn_exclusion_doc_ids": ["turn-1"],
        }
        return ctx

    def _context_resolve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        stabilized = ctx.artifacts["stabilized_turn_state"]
        utterance = stabilized["candidate_facts"][0]["value"]
        assert utterance == "Who am I?"
        ctx.artifacts["resolved_context"] = ResolvedContext(
            history_anchors=("commit.confirmed_user_facts:user_name=Sebastian",),
            ambiguity_flags=(),
            continuity_posture=ContinuityPosture.REEVALUATE,
            prior_intent=None,
        )
        return ctx

    def _intent_resolve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        assert ctx.artifacts["resolved_context"].history_anchors
        assert ctx.artifacts["stabilized_turn_state"]["candidate_facts"][0]["value"] == "Who am I?"
        ctx.state = replace(ctx.state, resolved_intent="memory_recall", classified_intent="memory_recall")
        return ctx

    def _retrieve_evidence(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["retrieval_result"] = {"posture": "scored_non_empty", "hit_count": 1}
        return ctx

    def _policy_decide(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        assert ctx.artifacts["resolved_context"].continuity_posture is ContinuityPosture.REEVALUATE
        assert ctx.artifacts["retrieval_result"]["posture"] == "scored_non_empty"
        return ctx

    def _answer_assemble(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_assembly_contract"] = AnswerCandidate(
            decision_class="answer_from_memory",
            rendered_class="answer_from_memory",
            retrieval_branch="memory_retrieval",
            rationale="memory evidence available",
            evidence_counts={"structured_facts": 1},
            pending_repair_state={"required": False, "reason": "none"},
            resolved_obligations=["repair_state_not_required"],
            remaining_obligations=[],
            confirmed_user_facts=["user_name=Sebastian"],
        )
        return ctx

    def _answer_validate(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_validation_contract"] = validate_answer_assembly_boundary(
            ctx.artifacts["answer_assembly_contract"]
        )
        return ctx

    def _answer_render(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_render_contract"] = render_answer(
            assembly=ctx.artifacts["answer_assembly_contract"],
            validation=ctx.artifacts["answer_validation_contract"],
            preferred_text="I remember your name from prior validated context.",
        )
        return ctx

    stages = [
        CanonicalStage("observe.turn", _observe_turn),
        CanonicalStage("encode.candidates", _encode_candidates),
        CanonicalStage("stabilize.pre_route", _stabilize_pre_route),
        CanonicalStage("context.resolve", _context_resolve),
        CanonicalStage("intent.resolve", _intent_resolve),
        CanonicalStage("retrieve.evidence", _retrieve_evidence),
        CanonicalStage("policy.decide", _policy_decide),
        CanonicalStage("answer.assemble", _answer_assemble),
        CanonicalStage("answer.validate", _answer_validate),
        CanonicalStage("answer.render", _answer_render),
        CanonicalStage("answer.commit", lambda ctx: ctx),
    ]

    final_context = CanonicalTurnOrchestrator(stages=stages).run(context)

    assert final_context.state.resolved_intent == "memory_recall"
    assert final_context.stage_audit_trail == list(CanonicalTurnOrchestrator.STAGE_ORDER)


def test_intent_resolve_fails_when_context_resolve_semantics_are_missing() -> None:
    state = PipelineState(user_input="who am i")
    context = CanonicalTurnContext(
        state=state,
        artifacts={
            "turn_observation": {"turn_id": "turn-1", "utterance": "who am i"},
            "encoded_candidates": {"facts": [{"key": "utterance_raw", "value": "who am i"}]},
            "stabilized_turn_state": {"candidate_facts": [{"key": "utterance_raw", "value": "who am i"}]},
        },
    )

    stages = [CanonicalStage(name, lambda ctx: ctx) for name in CanonicalTurnOrchestrator.STAGE_ORDER]

    with pytest.raises(RuntimeError, match="context.resolve must produce resolved_context artifact"):
        CanonicalTurnOrchestrator(stages=stages).run(context)


def test_policy_decide_fails_without_valid_stabilized_or_retrieval_posture_semantics() -> None:
    state = PipelineState(user_input="what is my name")
    context = CanonicalTurnContext(state=state)

    def _noop(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return ctx

    def _observe(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["turn_observation"] = {"turn_id": "turn-1", "utterance": "what is my name"}
        return ctx

    def _encode(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["encoded_candidates"] = {"facts": [{"key": "utterance_raw", "value": "what is my name"}]}
        return ctx

    def _stabilize(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["stabilized_turn_state"] = {"candidate_facts": [{"key": "utterance_raw", "value": "what is my name"}]}
        return ctx

    def _context(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["resolved_context"] = ResolvedContext(
            history_anchors=(),
            ambiguity_flags=(),
            continuity_posture=ContinuityPosture.REEVALUATE,
            prior_intent=None,
        )
        return ctx

    def _intent(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["stabilized_turn_state"] = {"candidate_facts": [{"key": "utterance_raw", "value": "MUTATED"}]}
        return ctx

    def _retrieve_invalid(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["retrieval_result"] = {"hit_count": 1}
        return ctx

    stages = [
        CanonicalStage("observe.turn", _observe),
        CanonicalStage("encode.candidates", _encode),
        CanonicalStage("stabilize.pre_route", _stabilize),
        CanonicalStage("context.resolve", _context),
        CanonicalStage("intent.resolve", _intent),
        CanonicalStage("retrieve.evidence", _retrieve_invalid),
        CanonicalStage("policy.decide", _noop),
        CanonicalStage("answer.assemble", _noop),
        CanonicalStage("answer.validate", _noop),
        CanonicalStage("answer.render", _noop),
        CanonicalStage("answer.commit", _noop),
    ]

    with pytest.raises(RuntimeError, match="policy.decide requires unmodified stabilized_turn_state contract"):
        CanonicalTurnOrchestrator(stages=stages).run(context)


def test_answer_render_fails_when_validated_semantics_are_mutated_after_validation() -> None:
    state = PipelineState(user_input="hello")
    context = CanonicalTurnContext(state=state)

    def _noop(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return ctx

    def _observe(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["turn_observation"] = {"turn_id": "turn-1", "utterance": "hello"}
        return ctx

    def _encode(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["encoded_candidates"] = {"facts": [{"key": "utterance_raw", "value": "hello"}]}
        return ctx

    def _stabilize(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["stabilized_turn_state"] = {"candidate_facts": [{"key": "utterance_raw", "value": "hello"}]}
        return ctx

    def _context(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["resolved_context"] = ResolvedContext(
            history_anchors=(),
            ambiguity_flags=(),
            continuity_posture=ContinuityPosture.REEVALUATE,
            prior_intent=None,
        )
        return ctx

    def _retrieve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["retrieval_result"] = {"posture": "empty_evidence"}
        return ctx

    def _assemble(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_assembly_contract"] = AnswerCandidate(
            decision_class="answer_from_memory",
            rendered_class="answer_from_memory",
            retrieval_branch="memory_retrieval",
            rationale="validated decision",
            evidence_counts={"structured_facts": 0},
            pending_repair_state={"required": False, "reason": "none"},
            resolved_obligations=["repair_state_not_required"],
            remaining_obligations=[],
            confirmed_user_facts=[],
        )
        return ctx

    def _validate_then_mutate(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_validation_contract"] = validate_answer_assembly_boundary(
            ctx.artifacts["answer_assembly_contract"]
        )
        ctx.artifacts["answer_assembly_contract"] = AnswerCandidate(
            decision_class="ask_for_clarification",
            rendered_class="ask_for_clarification",
            retrieval_branch="direct_answer",
            rationale="mutated after validation",
            evidence_counts={"structured_facts": 0},
            pending_repair_state={"required": False, "reason": "none"},
            resolved_obligations=["repair_state_not_required"],
            remaining_obligations=[],
            confirmed_user_facts=[],
        )
        return ctx

    stages = [
        CanonicalStage("observe.turn", _observe),
        CanonicalStage("encode.candidates", _encode),
        CanonicalStage("stabilize.pre_route", _stabilize),
        CanonicalStage("context.resolve", _context),
        CanonicalStage("intent.resolve", _noop),
        CanonicalStage("retrieve.evidence", _retrieve),
        CanonicalStage("policy.decide", _noop),
        CanonicalStage("answer.assemble", _assemble),
        CanonicalStage("answer.validate", _validate_then_mutate),
        CanonicalStage("answer.render", _noop),
        CanonicalStage("answer.commit", _noop),
    ]

    with pytest.raises(RuntimeError, match="answer.render detected class drift"):
        CanonicalTurnOrchestrator(stages=stages).run(context)


def test_policy_authority_is_not_written_before_policy_decide_stage() -> None:
    state = PipelineState(user_input="Who am I?")
    context = CanonicalTurnContext(state=state, artifacts={"policy_decision": None, "decision_object": None})

    def _noop(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        return ctx

    def _observe(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["turn_observation"] = {"turn_id": "turn-1", "utterance": "Who am I?"}
        return ctx

    def _encode(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["encoded_candidates"] = {"facts": [{"key": "utterance_raw", "value": "Who am I?"}]}
        return ctx

    def _stabilize(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["stabilized_turn_state"] = {"candidate_facts": [{"key": "utterance_raw", "value": "Who am I?"}]}
        return ctx

    def _context(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["resolved_context"] = ResolvedContext(
            history_anchors=("commit.confirmed_user_facts:user_name=Sebastian",),
            ambiguity_flags=(),
            continuity_posture=ContinuityPosture.REEVALUATE,
            prior_intent=None,
        )
        return ctx

    def _intent(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.state = replace(ctx.state, classified_intent="memory_recall", resolved_intent="memory_recall")
        ctx.artifacts["retrieval_requirement"] = {"requires_retrieval": True, "reason": "resolved_memory_recall_intent"}
        assert ctx.artifacts.get("policy_decision") is None
        assert ctx.artifacts.get("decision_object") is None
        return ctx

    def _retrieve(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        assert ctx.artifacts.get("policy_decision") is None
        assert ctx.artifacts.get("decision_object") is None
        ctx.artifacts["retrieval_result"] = {"posture": "scored_non_empty", "hit_count": 1}
        return ctx

    def _policy(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["policy_decision"] = {"retrieval_branch": "memory_retrieval"}
        ctx.artifacts["decision_object"] = {"decision_class": "answer_from_memory"}
        return ctx

    def _validate(ctx: CanonicalTurnContext) -> CanonicalTurnContext:
        ctx.artifacts["answer_validation_contract"] = type("Validation", (), {"passed": True})()
        return ctx

    stages = [
        CanonicalStage("observe.turn", _observe),
        CanonicalStage("encode.candidates", _encode),
        CanonicalStage("stabilize.pre_route", _stabilize),
        CanonicalStage("context.resolve", _context),
        CanonicalStage("intent.resolve", _intent),
        CanonicalStage("retrieve.evidence", _retrieve),
        CanonicalStage("policy.decide", _policy),
        CanonicalStage("answer.assemble", _noop),
        CanonicalStage("answer.validate", _validate),
        CanonicalStage("answer.render", _noop),
        CanonicalStage("answer.commit", _noop),
    ]

    final_context = CanonicalTurnOrchestrator(stages=stages).run(context)
    assert final_context.artifacts["policy_decision"] == {"retrieval_branch": "memory_retrieval"}
    assert final_context.artifacts["decision_object"] == {"decision_class": "answer_from_memory"}
