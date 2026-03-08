from testbot.answer_assembly import AnswerCandidate, assemble_answer_contract
from testbot.answer_commit import CommittedTurnState, commit_answer_stage
from testbot.answer_rendering import RenderedAnswer, render_answer
from testbot.answer_validation import ValidatedAnswer, validate_answer_assembly_boundary
from testbot.candidate_encoding import EncodedTurnCandidates, encode_turn_candidates
from testbot.context_resolution import ResolvedContext, resolve as resolve_context
from testbot.evidence_retrieval import EvidenceBundle, RetrievalResult, retrieval_result
from testbot.intent_resolution import IntentResolutionInput, ResolvedIntent, resolve as resolve_intent
from testbot.intent_router import IntentType
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionClass, DecisionObject, decide_from_evidence
from testbot.stabilization import StabilizedTurnState, stabilize_pre_route
from testbot.turn_observation import TurnObservation, observe_turn
from testbot.memory_strata import derive_segment_descriptor


def test_ac_0013_02_canonical_turn_pipeline_type_preserving_stage_io() -> None:
    """AC-0013-02 canonical turn pipeline: stage boundaries preserve typed objects."""

    state = PipelineState(user_input="My name is Sebastian")
    observation = observe_turn(
        state,
        turn_id="ac-0013-02-turn",
        observed_at="2026-03-08T00:00:00Z",
        speaker="user",
        channel="cli",
    )
    assert isinstance(observation, TurnObservation)

    encoded = encode_turn_candidates(state, observation=observation, rewritten_query="my name is sebastian")
    assert isinstance(encoded, EncodedTurnCandidates)

    segment = derive_segment_descriptor(utterance=observation.utterance, has_dialogue_state=bool(encoded.dialogue_state))
    next_state, stabilized = stabilize_pre_route(
        store=None,  # type: ignore[arg-type]
        state=state,
        observation=observation,
        encoded=encoded,
        response_plan={"pathway": "contract_test"},
        reflection_yaml="offline: true",
        segment=segment,
        store_doc_fn=lambda *args, **kwargs: None,
    )
    assert isinstance(stabilized, StabilizedTurnState)
    assert all(hasattr(candidate, "key") for candidate in stabilized.candidate_facts)

    context = resolve_context(utterance=observation.utterance, prior_pipeline_state=None)
    assert isinstance(context, ResolvedContext)

    resolved = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=stabilized,
            context=context,
            fallback_utterance=observation.utterance,
        )
    )
    assert isinstance(resolved, ResolvedIntent)

    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    assert isinstance(retrieval, RetrievalResult)

    decision = decide_from_evidence(intent=IntentType.KNOWLEDGE_QUESTION, retrieval=retrieval)
    assert isinstance(decision, DecisionObject)

    answer_candidate = assemble_answer_contract(decision=decision, evidence_bundle=retrieval.evidence_bundle)
    assert isinstance(answer_candidate, AnswerCandidate)

    validated = validate_answer_assembly_boundary(answer_candidate)
    assert isinstance(validated, ValidatedAnswer)

    rendered = render_answer(assembly=answer_candidate, validation=validated)
    assert isinstance(rendered, RenderedAnswer)

    committed_state, committed = commit_answer_stage(
        next_state,
        assembly=answer_candidate,
        validation=validated,
        rendered=rendered,
        commit_stage_id="answer.commit",
    )
    assert isinstance(committed, CommittedTurnState)
    assert committed_state.commit_receipt.get("committed") is True
    assert committed.commit_stage == "answer.commit"


def test_answer_validation_rejects_rendered_class_conflict() -> None:
    decision = DecisionObject(
        decision_class=DecisionClass.ANSWER_FROM_MEMORY,
        retrieval_branch="memory_retrieval",
        rationale="test",
    )
    candidate = assemble_answer_contract(decision=decision, evidence_bundle=EvidenceBundle())
    conflicted = AnswerCandidate(
        decision_class=candidate.decision_class,
        rendered_class="answer_general_knowledge_labeled",
        retrieval_branch=candidate.retrieval_branch,
        rationale=candidate.rationale,
        evidence_counts=candidate.evidence_counts,
        pending_repair_state=candidate.pending_repair_state,
        resolved_obligations=candidate.resolved_obligations,
        remaining_obligations=candidate.remaining_obligations,
        confirmed_user_facts=candidate.confirmed_user_facts,
    )

    validated = validate_answer_assembly_boundary(conflicted)

    assert validated.passed is False
    assert "decision_rendered_class_conflict" in validated.failures
