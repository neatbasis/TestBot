from __future__ import annotations

import pytest

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_commit import CommittedTurnState, commit_answer_stage
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.pipeline_state import PipelineState, ProvenanceType


def _assembly(*, confirmed_user_facts: list[str], pending_repair_state: dict[str, object] | None = None) -> AnswerCandidate:
    return AnswerCandidate(
        decision_class="answer_from_memory",
        rendered_class="answer_from_memory",
        retrieval_branch="memory_retrieval",
        rationale="test",
        evidence_counts={"structured_facts": 1},
        pending_repair_state=pending_repair_state
        or {
            "repair_required_by_policy": False,
            "repair_offered_to_user": False,
            "reason": "none",
        },
        pending_ingestion_request_id="",
        resolved_obligations=["answer_from_memory"],
        remaining_obligations=[],
        confirmed_user_facts=confirmed_user_facts,
    )


def test_committed_turn_state_confirmed_user_facts_match_stabilized_fact_candidates_exactly() -> None:
    state = PipelineState(
        user_input="My name is ava",
        candidate_facts={"facts": [{"key": "user_name", "value": "ava", "confidence": 0.95}]},
    )

    committed_state, committed = commit_answer_stage(
        state,
        assembly=_assembly(confirmed_user_facts=[]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="ok"),
    )

    assert isinstance(committed, CommittedTurnState)
    assert committed.confirmed_user_facts == ["name=Ava"]
    assert committed_state.commit_receipt.get("confirmed_user_facts") == ["name=Ava"]


def test_answer_provenance_mirrors_validated_evidence_bindings() -> None:
    validation = ValidatedAnswer(
        passed=True,
        failures=[],
        claims=["claim:timezone"],
        provenance_types=[ProvenanceType.MEMORY, ProvenanceType.SYSTEM_STATE],
        used_memory_refs=["mem:1"],
        used_source_evidence_refs=["src:2"],
        source_evidence_attribution=[{"source": "src:2", "supports": "claim:timezone"}],
    )

    committed_state, _ = commit_answer_stage(
        PipelineState(user_input="what timezone did i mention"),
        assembly=_assembly(confirmed_user_facts=["timezone=UTC"]),
        validation=validation,
        rendered=RenderedAnswer(rendered_text="You mentioned UTC."),
    )

    answer_provenance = {
        "claims": committed_state.claims,
        "provenance_types": committed_state.provenance_types,
        "used_memory_refs": committed_state.used_memory_refs,
        "used_source_evidence_refs": committed_state.used_source_evidence_refs,
        "source_evidence_attribution": committed_state.source_evidence_attribution,
    }

    assert answer_provenance == {
        "claims": ["claim:timezone"],
        "provenance_types": [ProvenanceType.MEMORY, ProvenanceType.SYSTEM_STATE],
        "used_memory_refs": ["mem:1"],
        "used_source_evidence_refs": ["src:2"],
        "source_evidence_attribution": [{"source": "src:2", "supports": "claim:timezone"}],
    }


@pytest.mark.parametrize(
    ("repair_offer_rendered", "expected_reason", "expect_updated_pending_repair"),
    [
        (True, "repair_offer_rendered", True),
        (False, "none", False),
    ],
)
def test_repair_decisions_control_updated_pending_repair(
    repair_offer_rendered: bool,
    expected_reason: str,
    expect_updated_pending_repair: bool,
) -> None:
    state = PipelineState(user_input="help me repair", pending_repair={"old": "value"})
    assembly = _assembly(
        confirmed_user_facts=[],
        pending_repair_state={
            "repair_required_by_policy": True,
            "repair_offered_to_user": False,
            "offer_type": "repair_offer_followup",
            "reason": "repair_required_by_policy",
        },
    )

    committed_state, committed = commit_answer_stage(
        state,
        assembly=assembly,
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(
            rendered_text="I can help with repair.",
            repair_offer_rendered=repair_offer_rendered,
            repair_followup_route="repair_offer_followup",
        ),
    )

    updated_pending_repair = committed_state.pending_repair.to_dict()

    if expect_updated_pending_repair:
        assert updated_pending_repair["repair_offered_to_user"] is True
        assert updated_pending_repair["reason"] == expected_reason
        assert updated_pending_repair["followup_route"] == "repair_offer_followup"
    else:
        assert updated_pending_repair == {}

    assert committed.pending_repair_state["reason"] == expected_reason


def test_prior_dialogue_state_updates_are_local_and_deterministic() -> None:
    prior_state = PipelineState(
        user_input="Turn 3",
        candidate_facts={
            "turn_id": "turn-003",
            "dialogue_state": [{"label": "self_identification", "turn_count": 3}],
            "facts": [{"key": "user_name", "value": "Ava"}],
        },
        pending_repair={"repair_offered_to_user": True, "reason": "carry-over"},
    )

    committed_state, _ = commit_answer_stage(
        prior_state,
        assembly=_assembly(confirmed_user_facts=[]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="ok", repair_offer_rendered=False),
    )

    assert prior_state.pending_repair.to_dict() == {"reason": "carry-over", "repair_offered_to_user": True}
    assert committed_state.pending_repair.to_dict() == {}
    assert committed_state.candidate_facts.to_dict() == prior_state.candidate_facts.to_dict()
    assert committed_state.candidate_facts.get("dialogue_state") == [{"label": "self_identification", "turn_count": 3}]


def test_persisted_facts_are_exactly_one_write_per_fact_candidate() -> None:
    state = PipelineState(
        user_input="My name is Ava and timezone is UTC",
        candidate_facts={
            "facts": [
                {"key": "user_name", "value": "Ava"},
            ]
        },
    )
    committed_state, committed = commit_answer_stage(
        state,
        assembly=_assembly(confirmed_user_facts=["timezone=UTC", "timezone=UTC", "name=Ava"]),
        validation=ValidatedAnswer(passed=True, failures=[]),
        rendered=RenderedAnswer(rendered_text="ok"),
    )

    persisted_facts = committed_state.commit_receipt.get("confirmed_user_facts")

    assert persisted_facts == ["timezone=UTC", "name=Ava"]
    assert committed.confirmed_user_facts == ["timezone=UTC", "name=Ava"]
    assert len(persisted_facts) == len(set(persisted_facts))
