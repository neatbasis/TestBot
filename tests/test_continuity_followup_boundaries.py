from __future__ import annotations

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_commit import commit_answer_stage
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.context_resolution import ContinuityPosture, resolve as resolve_context
from testbot.pipeline_state import PipelineState


def _assembly(*, remaining_obligations: list[str], pending_repair_state: dict[str, object] | None = None) -> AnswerCandidate:
    return AnswerCandidate(
        decision_class="continue_repair_reconstruction",
        rendered_class="continue_repair_reconstruction",
        retrieval_branch="memory_retrieval",
        rationale="continuity-test",
        evidence_counts={"structured_facts": 0},
        pending_repair_state=pending_repair_state
        or {
            "repair_required_by_policy": True,
            "repair_offered_to_user": False,
            "offer_type": "repair_offer_followup",
            "reason": "repair_required_by_policy",
            "followup_route": "repair_offer_followup",
        },
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=remaining_obligations,
        confirmed_user_facts=[],
    )


def test_clarification_followup_affirmation_preserves_continuity_across_turn_boundary() -> None:
    committed_state, _ = commit_answer_stage(
        PipelineState(user_input="can you continue?", resolved_intent="capabilities_help", prior_unresolved_intent="capabilities_help"),
        assembly=_assembly(remaining_obligations=["clarify_satellite_request"]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(
            rendered_text="Can you clarify whether you want me to continue via satellite?",
            repair_offer_rendered=True,
            repair_followup_route="repair_offer_followup",
        ),
    )

    followup = resolve_context(utterance="yes", prior_pipeline_state=committed_state)

    assert followup.continuity_posture is ContinuityPosture.PRESERVE_PRIOR_INTENT
    assert "clarification_continuity" in followup.history_anchors
    assert "commit.assistant_offer_anchor:followup_route=repair_offer_followup" in followup.history_anchors
    assert "commit.remaining_obligations:clarify_satellite_request" in followup.history_anchors


def test_repair_followup_continuity_resets_after_topic_shift_boundary() -> None:
    repair_committed_state, _ = commit_answer_stage(
        PipelineState(user_input="help repair timeline", resolved_intent="memory_recall", prior_unresolved_intent="memory_recall"),
        assembly=_assembly(remaining_obligations=["continue_repair_reconstruction"]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(
            rendered_text="I can help continue repair reconstruction from what we confirmed.",
            repair_offer_rendered=True,
            repair_followup_route="repair_offer_followup",
        ),
    )

    topic_shift_state, _ = commit_answer_stage(
        repair_committed_state,
        assembly=AnswerCandidate(
            decision_class="answer_general_knowledge_labeled",
            rendered_class="answer_general_knowledge_labeled",
            retrieval_branch="direct_answer",
            rationale="topic-shift",
            evidence_counts={"structured_facts": 0},
            pending_repair_state={"repair_required_by_policy": False, "repair_offered_to_user": False, "reason": "none"},
            pending_ingestion_request_id="",
            resolved_obligations=["repair_state_not_required"],
            remaining_obligations=[],
            confirmed_user_facts=[],
        ),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="Sure — different topic."),
    )

    delayed_followup = resolve_context(utterance="yes", prior_pipeline_state=topic_shift_state)

    assert delayed_followup.continuity_posture is ContinuityPosture.REEVALUATE
    assert "clarification_continuity" not in delayed_followup.history_anchors
    assert "commit.remaining_obligations:continue_repair_reconstruction" not in delayed_followup.history_anchors
