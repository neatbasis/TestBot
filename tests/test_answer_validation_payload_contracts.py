import pytest

from testbot.answer_assembly import AnswerCandidate, PendingRepairState
from testbot.answer_validation import validate_answer_assembly_boundary


def _assembly() -> AnswerCandidate:
    return AnswerCandidate(
        decision_class="answer_general_knowledge_labeled",
        rendered_class="answer_general_knowledge_labeled",
        retrieval_branch="direct_answer",
        rationale="test",
        evidence_counts={},
        pending_repair_state=PendingRepairState(repair_required_by_policy=False, repair_offered_to_user=False),
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )


def test_validation_boundary_coerces_invariant_and_alignment_to_typed_artifacts() -> None:
    validated = validate_answer_assembly_boundary(
        _assembly(),
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
        alignment_decision={"final_alignment_decision": "allow", "dimensions": {"safety": 1.0}},
    )

    assert validated.invariant_decisions is not None
    assert validated.alignment_decision is not None
    assert validated.invariant_decisions["answer_mode"] == "assist"
    assert validated.alignment_decision["final_alignment_decision"] == "allow"


def test_validation_boundary_rejects_invalid_alignment_dimension_inputs_shape() -> None:
    with pytest.raises(TypeError, match="dimension_inputs must be a mapping"):
        validate_answer_assembly_boundary(
            _assembly(),
            alignment_decision={"final_alignment_decision": "allow", "dimension_inputs": ["not-a-mapping"]},
        )
