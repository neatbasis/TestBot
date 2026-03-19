from __future__ import annotations

from testbot.answer_assembly import AnswerCandidate, PendingRepairState
from testbot.answer_commit import CommittedTurnState
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.domain import (
    AnswerCandidate as TypedAnswerCandidate,
    CommittedTurnState as TypedCommittedTurnState,
    IntentResolution,
    TurnObservation,
    answer_candidate_from_legacy,
    committed_turn_state_from_legacy,
)
from testbot.intent_resolution import ResolvedIntent
from testbot.intent_router import IntentType
from testbot.policy_decision import DecisionClass, decide
from testbot.turn_observation import TurnObservation as LegacyTurnObservation


def test_raw_vs_interpreted_distinction_is_preserved_in_typed_turn_observation() -> None:
    legacy = LegacyTurnObservation(
        turn_id="turn-1",
        utterance="  raw text? ",
        observed_at="2026-03-19T00:00:00+00:00",
        speaker="user",
        channel="cli",
        classified_intent="knowledge_question",
        resolved_intent="memory_recall",
    )

    typed = TurnObservation.from_legacy(legacy)

    assert typed.utterance == "  raw text? "
    assert typed.classified_intent == "knowledge_question"
    assert typed.resolved_intent == "memory_recall"


def test_candidate_vs_resolved_intent_distinction_is_typed() -> None:
    legacy = ResolvedIntent(
        classified_intent=IntentType.KNOWLEDGE_QUESTION,
        resolved_intent=IntentType.CAPABILITIES_HELP,
        rationale="repair continuity",
    )

    typed = IntentResolution.from_legacy(legacy)

    assert typed.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert typed.resolved_intent is IntentType.CAPABILITIES_HELP


def test_empty_evidence_vs_scored_empty_reasoning_distinction_is_deterministic() -> None:
    empty = decide(utterance="who am i", intent=IntentType.MEMORY_RECALL, retrieval_candidates_considered=0, hit_count=0)
    scored_empty = decide(utterance="who am i", intent=IntentType.MEMORY_RECALL, retrieval_candidates_considered=3, hit_count=0)

    assert empty.reasoning["empty_evidence"] is True
    assert empty.reasoning["scored_empty"] is False
    assert scored_empty.reasoning["empty_evidence"] is False
    assert scored_empty.reasoning["scored_empty"] is True


def test_validated_vs_degraded_distinction_is_explicit() -> None:
    validated = ValidatedAnswer(passed=True, failures=[], final_answer="ok")
    degraded = RenderedAnswer(rendered_text="[degraded:clarifier]...", degraded_response=True)

    assert validated.passed is True
    assert degraded.degraded_response is True


def test_rendered_offer_vs_committed_pending_repair_state_distinction() -> None:
    legacy_candidate = AnswerCandidate(
        decision_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED.value,
        rendered_class=DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED.value,
        retrieval_branch="direct_answer",
        rationale="offer-bearing",
        evidence_counts={},
        pending_repair_state=PendingRepairState(
            repair_required_by_policy=False,
            repair_offered_to_user=True,
            offer_type="capability_offer",
            reason="offer_bearing_answer",
        ),
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )
    typed_candidate: TypedAnswerCandidate = answer_candidate_from_legacy(legacy_candidate)
    assert typed_candidate.pending_repair_state.repair_offered_to_user is True

    committed = CommittedTurnState(
        turn_id="turn-1",
        commit_stage="answer.commit",
        rendered_text="text",
        pending_repair_state={
            "repair_required_by_policy": False,
            "repair_offered_to_user": True,
            "reason": "repair_offer_rendered",
            "followup_route": "capability_offer",
        },
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )
    typed_committed: TypedCommittedTurnState = committed_turn_state_from_legacy(committed)
    assert typed_committed.pending_repair_state.reason == "repair_offer_rendered"
    assert typed_committed.pending_repair_state.followup_route == "capability_offer"
