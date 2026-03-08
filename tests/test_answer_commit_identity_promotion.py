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
        pending_repair_state={"required": False, "reason": "none"},
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
