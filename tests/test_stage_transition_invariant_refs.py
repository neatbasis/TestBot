from __future__ import annotations

import json

from testbot.canonical_turn_orchestrator import CanonicalTurnOrchestrator
from testbot.pipeline_state import PipelineState
from testbot.stage_transitions import (
    LEGACY_STAGE_ALIAS_MAP,
    LEGACY_TO_PIPELINE_INVARIANT_REF_MAP,
    TRANSITION_VALIDATION_SCHEMA_VERSION,
    append_transition_validation_log,
    migrate_invariant_refs_to_pipeline_namespace,
    validate_answer_assemble_pre,
    validate_answer_commit_post,
    validate_answer_commit_pre,
    validate_answer_render_post,
    validate_answer_render_pre,
    validate_answer_validate_post,
    validate_answer_validate_pre,
    validate_context_resolve_post,
    validate_context_resolve_pre,
    validate_encode_candidates_post,
    validate_encode_candidates_pre,
    validate_intent_resolve_post,
    validate_intent_resolve_pre,
    validate_observe_turn_post,
    validate_observe_turn_pre,
    validate_policy_decide_post,
    validate_policy_decide_pre,
    validate_retrieve_evidence_post,
    validate_retrieve_evidence_pre,
    validate_stabilize_pre_route_post,
    validate_stabilize_pre_route_pre,
)


def _base_state() -> PipelineState:
    return PipelineState(
        user_input="What did I say yesterday?",
        rewritten_query="yesterday user utterance",
        confidence_decision={"context_confident": True},
        draft_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        final_answer="You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z",
        candidate_facts={"utterance_raw": "What did I say yesterday?", "segment_id": "segment-1"},
        resolved_context={"history_anchors": ["turn-1"]},
        resolved_intent="memory_recall",
        retrieval_candidates=[],
        reranked_hits=[],
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
    observe_result = validate_observe_turn_pre(_base_state())
    answer_result = validate_answer_commit_post(_base_state())

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


def test_transition_validation_log_rows_use_schema_version_3_and_canonical_stage_names(tmp_path) -> None:
    result = validate_observe_turn_pre(_base_state())
    log_path = tmp_path / "session.jsonl"

    append_transition_validation_log(result, log_path=log_path)

    row = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert row["event"] == "stage_transition_validation"
    assert row["schema_version"] == TRANSITION_VALIDATION_SCHEMA_VERSION == 3
    assert row["stage"] == "observe.turn"
    assert row["legacy_stage"] == LEGACY_STAGE_ALIAS_MAP["observe.turn"] == "observe"
    assert row["invariant_refs"] == ["PINV-002"]


def test_every_canonical_stage_has_transition_validation_boundary_check() -> None:
    state = _base_state()
    results = [
        validate_observe_turn_pre(state),
        validate_observe_turn_post(state),
        validate_encode_candidates_pre(state),
        validate_encode_candidates_post(state),
        validate_stabilize_pre_route_pre(state),
        validate_stabilize_pre_route_post(state),
        validate_context_resolve_pre(state),
        validate_context_resolve_post(state),
        validate_intent_resolve_pre(state),
        validate_intent_resolve_post(state),
        validate_retrieve_evidence_pre(state),
        validate_retrieve_evidence_post(state),
        validate_policy_decide_pre(state),
        validate_policy_decide_post(state),
        validate_answer_assemble_pre(state),
        validate_answer_validate_pre(state),
        validate_answer_validate_post(state),
        validate_answer_render_pre(state),
        validate_answer_render_post(state),
        validate_answer_commit_pre(state),
        validate_answer_commit_post(state),
    ]
    stages_with_checks = {result.stage for result in results}

    assert stages_with_checks == set(CanonicalTurnOrchestrator.STAGE_ORDER)
