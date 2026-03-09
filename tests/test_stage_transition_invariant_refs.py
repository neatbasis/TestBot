from __future__ import annotations

import json

from testbot.canonical_turn_orchestrator import CanonicalTurnOrchestrator
from testbot.pipeline_state import CandidateFactsArtifact, PipelineState, ResolvedContextArtifact
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
        validate_answer_validate_post(state, {"answer_validation_contract": {"passed": True}}),
        validate_answer_render_pre(state),
        validate_answer_render_post(state),
        validate_answer_commit_pre(state),
        validate_answer_commit_post(state),
    ]
    stages_with_checks = {result.stage for result in results}

    assert stages_with_checks == set(CanonicalTurnOrchestrator.STAGE_ORDER)


def test_typed_artifact_wrappers_pass_stabilize_and_context_transition_checks() -> None:
    state = PipelineState(
        user_input="What did I say yesterday?",
        rewritten_query="yesterday user utterance",
        candidate_facts=CandidateFactsArtifact(facts=[{"key": "utterance_raw", "value": "What did I say yesterday?"}]),
        resolved_context=ResolvedContextArtifact(entities=[{"kind": "user", "value": "me"}]),
    )

    assert validate_stabilize_pre_route_post(state).passed
    assert validate_context_resolve_pre(state).passed
    assert validate_context_resolve_post(state).passed
    assert validate_intent_resolve_pre(state).passed


def test_stabilize_pre_route_post_accepts_populated_candidate_facts_artifact() -> None:
    state = PipelineState(
        user_input="What did I say yesterday?",
        rewritten_query="yesterday user utterance",
        candidate_facts=CandidateFactsArtifact(
            facts=[{"key": "utterance_raw", "value": "What did I say yesterday?", "confidence": 1.0}]
        ),
    )

    result = validate_stabilize_pre_route_post(state)

    assert result.passed
    assert result.failures == ()


def test_answer_validate_pre_accepts_artifact_handoff_without_state_draft_answer() -> None:
    state = PipelineState(user_input="What did I say yesterday?", confidence_decision={"context_confident": True})

    assembled = type("Assembled", (), {"draft_answer": "You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z"})()
    result = validate_answer_validate_pre(state, {"assembled_answer": assembled})

    assert result.passed
    assert result.failures == ()


def test_answer_render_and_commit_pre_accept_artifact_handoff_without_state_final_answer() -> None:
    state = PipelineState(user_input="What did I say yesterday?")

    validated = type("Validated", (), {"final_answer": "You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z"})()
    rendered = type("Rendered", (), {"final_answer": "You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z"})()

    render_pre = validate_answer_render_pre(state, {"validated_answer": validated})
    commit_pre = validate_answer_commit_pre(state, {"rendered_answer": rendered})

    assert render_pre.passed
    assert commit_pre.passed


def test_answer_assemble_to_validate_sequence_uses_artifact_contract() -> None:
    state = PipelineState(
        user_input="What did I say yesterday?",
        confidence_decision={"context_confident": True},
        draft_answer="",
    )

    assemble_pre = validate_answer_assemble_pre(state)
    assert assemble_pre.passed

    assembled = type("Assembled", (), {"draft_answer": "You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z"})()
    validate_pre = validate_answer_validate_pre(state, {"assembled_answer": assembled})

    assert validate_pre.passed
    assert validate_pre.failures == ()


def test_answer_validate_pre_accepts_answer_assembly_contract_without_state_draft_answer() -> None:
    state = PipelineState(user_input="What did I say yesterday?", confidence_decision={"context_confident": True})

    result = validate_answer_validate_pre(state, {"answer_assembly_contract": {"decision_class": "answer_from_memory"}})

    assert result.passed
    assert result.failures == ()

def test_answer_validate_post_allows_empty_final_answer_when_validation_artifact_present() -> None:
    state = PipelineState(user_input="What did I say yesterday?")

    result = validate_answer_validate_post(
        state,
        {"answer_validation_contract": {"passed": True, "failures": []}, "validated_answer": object()},
    )

    assert result.passed
    assert result.failures == ()


def test_answer_validate_post_fails_when_validation_artifact_missing() -> None:
    state = PipelineState(user_input="What did I say yesterday?")

    result = validate_answer_validate_post(state)

    assert not result.passed
    assert result.failures == ("validation_artifact_present",)


def test_answer_render_post_accepts_artifact_handoff_before_state_final_answer_commit() -> None:
    state = PipelineState(user_input="What did I say yesterday?")

    rendered = type("Rendered", (), {"final_answer": "You said hi. doc_id: 1 ts: 2025-01-01T00:00:00Z"})()
    result = validate_answer_render_post(state, {"rendered_answer": rendered})

    assert result.passed
    assert result.failures == ()
