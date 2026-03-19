import pytest

from testbot.pipeline_state import AlignmentDecision, CommitReceiptArtifact, ConfidenceDecision


def test_confidence_decision_required_scored_candidates_key_raises() -> None:
    decision = ConfidenceDecision.from_mapping({"context_confident": True})

    with pytest.raises(KeyError):
        decision.typed_scored_candidates(required=True)


def test_confidence_decision_scored_candidates_type_is_enforced() -> None:
    with pytest.raises(TypeError, match="scored_candidates must be a list"):
        ConfidenceDecision.from_mapping({"scored_candidates": "not-a-list"})


def test_alignment_decision_required_dimension_inputs_key_raises() -> None:
    decision = AlignmentDecision.from_mapping({"final_alignment_decision": "allow"})

    with pytest.raises(KeyError):
        decision.typed_dimension_inputs(required=True)


def test_alignment_decision_dimension_inputs_type_is_enforced() -> None:
    with pytest.raises(TypeError, match="dimension_inputs must be a mapping"):
        AlignmentDecision.from_mapping({"dimension_inputs": ["bad"]})


def test_commit_receipt_contract_types_are_enforced() -> None:
    with pytest.raises(TypeError, match="resolved_obligations must be a list"):
        CommitReceiptArtifact.from_mapping({"resolved_obligations": {"bad": True}})
