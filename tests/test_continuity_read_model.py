from __future__ import annotations

from testbot.continuity_read_model import (
    continuity_context_anchors,
    continuity_prior_intent_hint,
    continuity_read_model_from_pipeline_state,
    continuity_retrieval_anchors,
)
from testbot.pipeline_state import PipelineState


def test_continuity_read_model_projects_cross_turn_authority_from_pipeline_state() -> None:
    prior_state = PipelineState(
        user_input="follow up",
        resolved_intent="knowledge_question",
        prior_unresolved_intent="memory_recall",
        commit_receipt={
            "committed": True,
            "turn_id": "turn-1",
            "commit_stage": "answer.commit",
            "pending_ingestion_request_id": "ingest-7",
            "pending_repair_state": {
                "repair_offered_to_user": True,
                "followup_route": "repair_offer_followup",
                "offer_type": "capability_offer",
                "obligation_id": "repair-2",
            },
            "resolved_obligations": ["done-1"],
            "remaining_obligations": ["todo-1"],
            "confirmed_user_facts": ["name=Sam"],
        },
        pending_clarification={
            "required": True,
            "question": "Which Sam?",
            "obligation_id": "clarify-3",
            "source_anchor": "commit.pending_clarification",
            "focus": "person",
        },
    )

    continuity = continuity_read_model_from_pipeline_state(prior_state)

    assert continuity is not None
    assert continuity.committed_turn is not None
    assert continuity.committed_turn.turn_id == "turn-1"
    assert continuity.committed_turn.pending_repair_state.obligation_id == "repair-2"
    assert continuity.pending_clarification is not None
    assert continuity.pending_clarification.obligation_id == "clarify-3"
    assert continuity.interpretation.prior_unresolved_intent == "memory_recall"
    assert continuity.interpretation.resolved_intent_fallback == "knowledge_question"


def test_continuity_prior_intent_hint_keeps_policy_owned_value_primary_with_compat_fallback() -> None:
    policy_owned = continuity_read_model_from_pipeline_state(
        PipelineState(user_input="x", resolved_intent="knowledge_question", prior_unresolved_intent="memory_recall")
    )
    compatibility_only = continuity_read_model_from_pipeline_state(
        PipelineState(user_input="x", resolved_intent="knowledge_question", prior_unresolved_intent="")
    )

    assert continuity_prior_intent_hint(policy_owned) == "memory_recall"
    assert continuity_prior_intent_hint(compatibility_only) == "knowledge_question"


def test_continuity_anchor_builders_share_core_inputs_but_keep_context_only_offer_metadata() -> None:
    continuity = continuity_read_model_from_pipeline_state(
        PipelineState(
            user_input="x",
            commit_receipt={
                "confirmed_user_facts": ["name=Sam"],
                "pending_repair_state": {
                    "repair_offered_to_user": True,
                    "followup_route": "repair_offer_followup",
                    "offer_type": "capability_offer",
                    "obligation_id": "repair-2",
                },
            },
            pending_clarification={"required": True, "obligation_id": "clarify-4", "focus": "person"},
        )
    )

    context_anchors = continuity_context_anchors(continuity)
    retrieval_anchors = continuity_retrieval_anchors(continuity)

    assert "commit.assistant_offer_anchor:followup_route=repair_offer_followup" in context_anchors
    assert "commit.assistant_offer_anchor:followup_route=repair_offer_followup" not in retrieval_anchors
    assert "commit.pending_clarification:obligation_id=clarify-4" in context_anchors
    assert "commit.pending_clarification:obligation_id=clarify-4" in retrieval_anchors
