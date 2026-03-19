from testbot.candidate_encoding import EncodedTurnCandidates
from testbot.memory_strata import SegmentDescriptor, SegmentType
from testbot.pipeline_state import PipelineState
from testbot.stabilization import build_stabilization_plan
from testbot.turn_observation import TurnObservation
from testbot.evidence_retrieval import continuity_evidence_from_prior_state


def _observation(turn_id: str, utterance: str) -> TurnObservation:
    return TurnObservation(
        turn_id=turn_id,
        utterance=utterance,
        observed_at="2026-03-12T10:00:00Z",
        speaker="user",
        channel="cli",
        classified_intent="knowledge_question",
        resolved_intent="knowledge_question",
    )


def test_stabilization_carries_pending_clarification_with_durable_id() -> None:
    state = PipelineState(
        user_input="follow up",
        pending_clarification={
            "required": True,
            "question": "Which one?",
            "obligation_id": "clarify-7",
            "source_anchor": "commit.pending_clarification",
            "focus": "person",
        },
    )

    plan = build_stabilization_plan(
        state=state,
        observation=_observation("turn-2", "Alex"),
        encoded=EncodedTurnCandidates(rewritten_query="Alex"),
        response_plan={},
        reflection_yaml="x: y",
        segment=SegmentDescriptor(segment_type=SegmentType.CONTIGUOUS_TOPIC, segment_id="seg-a", continuity_key="person"),
    )

    assert plan.stabilized.pending_clarification is not None
    assert plan.stabilized.pending_clarification.obligation_id == "clarify-7"
    assert plan.next_state.pending_clarification.get("obligation_id") == "clarify-7"


def test_continuity_evidence_includes_pending_clarification_and_repair_ids() -> None:
    state = PipelineState(
        user_input="x",
        pending_clarification={
            "required": True,
            "obligation_id": "clarify-9",
            "focus": "time_window",
        },
        commit_receipt={
            "pending_repair_state": {
                "repair_offered_to_user": True,
                "obligation_id": "repair-2",
            }
        },
    )

    anchors = continuity_evidence_from_prior_state(state)

    assert "commit.pending_clarification:required" in anchors
    assert "commit.pending_clarification:obligation_id=clarify-9" in anchors
    assert "commit.pending_repair_state:obligation_id=repair-2" in anchors
