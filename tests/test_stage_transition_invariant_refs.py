from __future__ import annotations

import json

from testbot.pipeline_state import PipelineState
from testbot.stage_transitions import (
    LEGACY_TO_PIPELINE_INVARIANT_REF_MAP,
    TRANSITION_VALIDATION_SCHEMA_VERSION,
    append_transition_validation_log,
    migrate_invariant_refs_to_pipeline_namespace,
    validate_answer_post,
    validate_observe_pre,
)


def _base_state() -> PipelineState:
    return PipelineState(
        user_input="What did I say yesterday?",
        rewritten_query="yesterday user utterance",
        confidence_decision={"context_confident": True},
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        invariant_decisions={
            "response_contains_claims": True,
            "has_required_memory_citation": True,
            "answer_contract_valid": True,
            "answer_mode": "memory-grounded",
        },
        claims=["You said hi yesterday."],
        alignment_decision={
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 1.0,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "allow",
        },
    )


def test_stage_transition_validators_emit_pipeline_invariant_namespace() -> None:
    observe_result = validate_observe_pre(_base_state())
    answer_result = validate_answer_post(_base_state())

    assert observe_result.invariant_refs == ("PINV-002",)
    assert answer_result.invariant_refs == ("PINV-001", "PINV-002", "PINV-003")


def test_migration_map_normalizes_legacy_transition_invariant_refs() -> None:
    assert LEGACY_TO_PIPELINE_INVARIANT_REF_MAP == {
        "INV-001": "PINV-001",
        "INV-002": "PINV-002",
        "INV-003": "PINV-003",
    }
    assert migrate_invariant_refs_to_pipeline_namespace(("INV-001", "INV-002", "PINV-003")) == (
        "PINV-001",
        "PINV-002",
        "PINV-003",
    )


def test_transition_validation_log_rows_use_schema_version_3_and_pipeline_ids(tmp_path) -> None:
    result = validate_observe_pre(_base_state())
    log_path = tmp_path / "session.jsonl"

    append_transition_validation_log(result, log_path=log_path)

    row = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert row["event"] == "stage_transition_validation"
    assert row["schema_version"] == TRANSITION_VALIDATION_SCHEMA_VERSION == 3
    assert row["invariant_refs"] == ["PINV-002"]
