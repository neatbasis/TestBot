from testbot.answer_assembly import AnswerCandidate
from testbot.answer_commit import commit_answer_stage
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.context_resolution import resolve as resolve_context
from testbot.pipeline_state import PipelineState


def _base_assembly(*, confirmed_user_facts: list[str]) -> AnswerCandidate:
    return AnswerCandidate(
        decision_class="answer_from_memory",
        rendered_class="answer_from_memory",
        retrieval_branch="memory_retrieval",
        rationale="test",
        evidence_counts={
            "structured_facts": 0,
            "episodic_utterances": 0,
            "repair_anchors_offers": 0,
            "reflections_hypotheses": 0,
            "source_evidence": 0,
        },
        pending_repair_state={"repair_required_by_policy": False, "repair_offered_to_user": False, "reason": "none"},
        pending_ingestion_request_id="",
        resolved_obligations=["repair_state_not_required"],
        remaining_obligations=[],
        confirmed_user_facts=confirmed_user_facts,
    )


def test_commit_promotes_stabilized_identity_fact_into_receipt() -> None:
    state = PipelineState(
        user_input="My name is sam",
        candidate_facts={
            "facts": [
                {"key": "utterance_raw", "value": "My name is sam", "confidence": 1.0},
                {"key": "user_name", "value": "sam", "confidence": 0.95},
            ]
        },
    )

    committed_state, committed = commit_answer_stage(
        state,
        assembly=_base_assembly(confirmed_user_facts=[]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="ok"),
    )

    assert committed_state.commit_receipt.get("confirmed_user_facts") == ["name=Sam"]
    assert committed.confirmed_user_facts == ["name=Sam"]


def test_commit_does_not_promote_identity_when_contradicted_by_confirmed_fact() -> None:
    state = PipelineState(
        user_input="My name is sam",
        candidate_facts={
            "facts": [{"key": "user_name", "value": "sam", "confidence": 0.95}]
        },
    )

    committed_state, committed = commit_answer_stage(
        state,
        assembly=_base_assembly(confirmed_user_facts=["name=Taylor"]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="ok"),
    )

    assert committed_state.commit_receipt.get("confirmed_user_facts") == ["name=Taylor"]
    assert committed.confirmed_user_facts == ["name=Taylor"]


def test_promoted_identity_fact_is_available_as_next_turn_continuity_anchor() -> None:
    state = PipelineState(
        user_input="My name is sam",
        candidate_facts={"facts": [{"key": "user_name", "value": "sam", "confidence": 0.95}]},
    )
    committed_state, _ = commit_answer_stage(
        state,
        assembly=_base_assembly(confirmed_user_facts=[]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="ok"),
    )

    next_context = resolve_context(utterance="who am i?", prior_pipeline_state=committed_state)

    assert "commit.confirmed_user_facts:name=Sam" in next_context.history_anchors


def test_uncertainty_fallback_without_explicit_offer_clears_pending_repair() -> None:
    state = PipelineState(user_input="who am i")
    committed_state, committed = commit_answer_stage(
        state,
        assembly=AnswerCandidate(
            decision_class="pending_lookup_background_ingestion",
            rendered_class="pending_lookup_background_ingestion",
            retrieval_branch="memory_retrieval",
            rationale="repair required by policy",
            evidence_counts={"structured_facts": 0},
            pending_repair_state={
                "repair_required_by_policy": True,
                "repair_offered_to_user": False,
                "reason": "repair_required_by_policy",
            },
            pending_ingestion_request_id="ing-1",
            resolved_obligations=[],
            remaining_obligations=["pending_lookup_background_ingestion"],
            confirmed_user_facts=[],
        ),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="I don't know from memory."),
    )

    assert committed_state.pending_repair.to_dict() == {}
    assert committed.pending_repair_state["repair_required_by_policy"] is True
    assert committed.pending_repair_state["repair_offered_to_user"] is False
    assert committed.pending_repair_state["reason"] == "none"


def test_explicit_repair_offer_sets_pending_repair_and_followup_route() -> None:
    state = PipelineState(user_input="who am i")
    committed_state, committed = commit_answer_stage(
        state,
        assembly=AnswerCandidate(
            decision_class="continue_repair_reconstruction",
            rendered_class="continue_repair_reconstruction",
            retrieval_branch="memory_retrieval",
            rationale="repair required by policy",
            evidence_counts={"structured_facts": 0},
            pending_repair_state={
                "repair_required_by_policy": True,
                "repair_offered_to_user": False,
                "reason": "repair_required_by_policy",
            },
            pending_ingestion_request_id="",
            resolved_obligations=[],
            remaining_obligations=["continue_repair_reconstruction"],
            confirmed_user_facts=[],
        ),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(
            rendered_text="I can help continue repair reconstruction from what we confirmed.",
            repair_offer_rendered=True,
            repair_followup_route="repair_offer_followup",
        ),
    )

    assert committed_state.pending_repair.to_dict()["repair_offered_to_user"] is True
    assert committed.pending_repair_state["followup_route"] == "repair_offer_followup"



def test_runtime_offer_phrase_keeps_commit_repair_offer_propagation_intact() -> None:
    state = PipelineState(user_input="what is ontology?")
    committed_state, committed = commit_answer_stage(
        state,
        assembly=AnswerCandidate(
            decision_class="answer_general_knowledge_labeled",
            rendered_class="answer_general_knowledge_labeled",
            retrieval_branch="direct_answer",
            rationale="offer-bearing answer",
            evidence_counts={"structured_facts": 0},
            pending_repair_state={
                "repair_required_by_policy": False,
                "repair_offered_to_user": True,
                "offer_type": "capability_offer",
                "reason": "offer_bearing_answer",
            },
            pending_ingestion_request_id="",
            resolved_obligations=["repair_state_not_required"],
            remaining_obligations=[],
            confirmed_user_facts=[],
        ),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(
            rendered_text=(
                "I can either help you reconstruct the timeline from what you remember, "
                "or suggest where to check next for the missing detail."
            ),
            repair_offer_rendered=True,
            repair_followup_route="capability_offer",
        ),
    )

    assert committed.pending_repair_state["repair_offered_to_user"] is True
    assert committed.pending_repair_state["followup_route"] == "capability_offer"
    assert committed_state.commit_receipt["pending_repair_state"]["repair_offered_to_user"] is True
