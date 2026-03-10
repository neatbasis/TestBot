from testbot.context_resolution import ContinuityPosture, resolve as resolve_context
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.intent_router import IntentType
from testbot.candidate_encoding import FactCandidate
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import EvidencePosture, decide
from testbot.sat_chatbot_memory_v2 import ROUTE_TO_ASK_ANSWER
from testbot.stabilization import StabilizedTurnState


def _stabilized(utterance: str) -> StabilizedTurnState:
    return StabilizedTurnState(
        turn_id="turn-1",
        utterance_card="UTTERANCE CARD",
        utterance_doc_id="u1",
        reflection_doc_id="r1",
        dialogue_state_doc_id="d1",
        segment_type="episodic",
        segment_id="seg-1",
        segment_membership_edge_refs=[],
        same_turn_exclusion_doc_ids=[],
        candidate_facts=[FactCandidate(key="utterance_raw", value=utterance, confidence=1.0)],
        candidate_speech_acts=[],
        candidate_dialogue_state=[],
        candidate_repairs=[],
    )


def test_context_resolution_exposes_typed_continuity_inputs() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    context = resolve_context(utterance="yes", prior_pipeline_state=prior_state)

    assert context.prior_intent is IntentType.CAPABILITIES_HELP
    assert context.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT
    assert "clarification_continuity" in context.history_anchors
    assert "short_affirmation" in context.ambiguity_flags


def test_intent_resolution_consumes_context_continuity_posture() -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )

    affirmative = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("yes"),
            context=resolve_context(utterance="yes", prior_pipeline_state=prior_state),
            fallback_utterance="yes",
        )
    )
    non_affirmative = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("what is ontology?"),
            context=resolve_context(utterance="what is ontology?", prior_pipeline_state=prior_state),
            fallback_utterance="what is ontology?",
        )
    )

    assert affirmative.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert affirmative.resolved_intent is IntentType.CAPABILITIES_HELP
    assert non_affirmative.resolved_intent is IntentType.KNOWLEDGE_QUESTION


def test_policy_decision_derives_empty_vs_scored_empty_posture() -> None:
    empty = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    scored_empty = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=4,
        hit_count=0,
    )

    assert empty.retrieval_branch == "memory_retrieval"
    assert empty.evidence_posture is EvidencePosture.EMPTY_EVIDENCE
    assert scored_empty.evidence_posture is EvidencePosture.SCORED_EMPTY


def test_turn_one_identity_declaration_not_routed_as_generic_knowledge_question() -> None:
    context = resolve_context(utterance="My name is Sam", prior_pipeline_state=None)
    turn_one = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("My name is Sam"),
            context=context,
            fallback_utterance="My name is Sam",
        )
    )

    assert turn_one.classified_intent is IntentType.META_CONVERSATION
    assert turn_one.resolved_intent is IntentType.META_CONVERSATION


def test_turn_two_who_am_i_with_continuity_prefers_memory_aware_intent() -> None:
    prior_state = PipelineState(
        user_input="My name is Sam",
        final_answer="Thanks Sam — I will remember that.",
        resolved_intent=IntentType.META_CONVERSATION.value,
        prior_unresolved_intent=IntentType.META_CONVERSATION.value,
        commit_receipt={
            "committed": True,
            "commit_id": "commit-1",
            "confirmed_user_facts": ["name=Sam"],
        },
    )

    context = resolve_context(utterance="Who am I?", prior_pipeline_state=prior_state)
    turn_two = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("Who am I?"),
            context=context,
            fallback_utterance="Who am I?",
        )
    )
    decision = decide(
        utterance="Who am I?",
        intent=turn_two.resolved_intent,
    )

    assert turn_two.classified_intent is IntentType.MEMORY_RECALL
    assert turn_two.resolved_intent is IntentType.MEMORY_RECALL
    assert decision.retrieval_branch == "memory_retrieval"


def test_knowledge_followup_with_repair_offer_anchor_promotes_to_capabilities_help() -> None:
    prior_state = PipelineState(
        user_input="What is life?",
        final_answer="I can look that up if you want.",
        resolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        prior_unresolved_intent=IntentType.KNOWLEDGE_QUESTION.value,
        commit_receipt={
            "committed": True,
            "commit_id": "commit-1",
            "pending_repair_state": {
                "repair_required_by_policy": False,
                "repair_offered_to_user": True,
                "reason": "offer_bearing_answer",
                "offer_type": "capability_offer",
            },
        },
    )

    context = resolve_context(utterance="define the term", prior_pipeline_state=prior_state)
    resolved = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized("define the term"),
            context=context,
            fallback_utterance="define the term",
        )
    )

    assert "commit.pending_repair_state:repair_offered_to_user" in context.history_anchors
    assert resolved.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert resolved.resolved_intent is IntentType.CAPABILITIES_HELP
