from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_RELEASE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aggregate_turn_analytics.py"
_spec = importlib.util.spec_from_file_location("aggregate_turn_analytics", _RELEASE_PATH)
assert _spec and _spec.loader
aggregator = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aggregator
_spec.loader.exec_module(aggregator)


def test_aggregate_turn_dataset_from_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "session_events_fixture.jsonl"
    rows = [json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines() if line.strip()]

    dataset = aggregator.aggregate_turn_dataset(rows)

    assert len(dataset) == 2
    assert dataset[0].intent == "memory_recall"
    assert dataset[0].action == "NONE"
    assert dataset[0].provenance_completeness == 1.0
    assert dataset[1].intent == "knowledge_question"
    assert dataset[1].action == "ASK_CLARIFYING_QUESTION"
    assert dataset[1].followup_proxy == 1.0
    assert dataset[1].provenance_completeness == 0.0


def test_compute_kpis_is_deterministic() -> None:
    dataset = [
        aggregator.TurnAnalytics(
            turn_index=1,
            intent="memory_recall",
            ambiguity_score=0.2,
            action="NONE",
            followup_proxy=0.2,
            provenance_completeness=1.0,
        ),
        aggregator.TurnAnalytics(
            turn_index=2,
            intent="knowledge_question",
            ambiguity_score=0.9,
            action="ASK_CLARIFYING_QUESTION",
            followup_proxy=1.0,
            provenance_completeness=0.0,
        ),
    ]

    kpis = aggregator.compute_kpis(dataset)

    assert kpis == {
        "grounded_answer_precision": 1.0,
        "false_knowing_rate": 0.0,
        "fallback_appropriateness": 1.0,
        "citation_completeness": 0.5,
        "turn_count": 2,
    }


def test_normalize_and_validate_rows_accepts_v1_v2_v3_analytics_events() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "legacy row"},
        {
            "event": "intent_classified",
            "schema_version": 2,
            "intent": "memory_recall",
            "ambiguity_score": 0.3,
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.3,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["memory"],
            "used_memory_refs": [{"doc_id": "abc"}],
            "basis_statement": "derived from memory",
        },
    ]

    normalized_rows, summary = aggregator.normalize_and_validate_rows(rows)

    assert len(normalized_rows) == 4
    assert normalized_rows[0]["schema_version"] == 1
    assert summary.invalid_rows == 0
    assert summary.skipped_rows == 0
    assert summary.per_event_validation_failures == {}


def test_normalize_and_validate_rows_skips_malformed_analytics_events() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "ok"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": "3",
            "intent": "memory_recall",
            "ambiguity_score": 0.2,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.0,
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": [],
            "used_memory_refs": [],
        },
    ]

    normalized_rows, summary = aggregator.normalize_and_validate_rows(rows)

    assert len(normalized_rows) == 1
    assert summary.invalid_rows == 3
    assert summary.skipped_rows == 3
    assert summary.per_event_validation_failures == {
        "intent_classified": 1,
        "fallback_action_selected": 1,
        "provenance_summary": 1,
    }


def test_missing_required_keys_are_not_silently_defaulted() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "turn 1"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "ambiguity_score": 0.1,
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.1,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.1,
        },
    ]

    normalized_rows, summary = aggregator.normalize_and_validate_rows(rows)
    dataset = aggregator.aggregate_turn_dataset(normalized_rows)

    assert summary.invalid_rows == 1
    assert summary.per_event_validation_failures == {"intent_classified": 1}
    assert dataset[0].intent == "memory_recall"


def test_aggregate_turn_dataset_supports_repair_continuation_action_deterministically() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "continue fixing"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.8,
            "user_followup_signal_proxy": 0.8,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.8,
            "chosen_action": "CONTINUE_REPAIR_RECONSTRUCTION",
            "user_followup_signal_proxy": 0.8,
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["mem-1"],
            "basis_statement": "repair continuation uses memory anchors",
        },
        {
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"required": True},
            "confirmed_user_facts": ["name=Sam"],
        },
    ]

    normalized_rows, _summary = aggregator.normalize_and_validate_rows(rows)
    dataset = aggregator.aggregate_turn_dataset(normalized_rows)

    assert len(dataset) == 1
    assert dataset[0].action == "CONTINUE_REPAIR_RECONSTRUCTION"
    assert dataset[0].provenance_completeness == 1.0


def test_normalize_and_validate_rows_accepts_pipeline_snapshot_sidecars_without_regression() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "hello"},
        {
            "event": "pipeline_state_snapshot",
            "schema_version": 3,
            "stage": "answer.commit",
            "state": {
                "commit_receipt": {
                    "commit_stage": "answer.commit",
                    "pending_repair_state": {"required": False},
                    "resolved_obligations": ["repair_state_not_required"],
                    "remaining_obligations": [],
                    "confirmed_user_facts": ["name=Sam"],
                }
            },
        },
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.1,
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.1,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["mem-1"],
            "basis_statement": "memory evidence",
        },
    ]

    normalized_rows, summary = aggregator.normalize_and_validate_rows(rows)
    dataset = aggregator.aggregate_turn_dataset(normalized_rows)

    assert summary.invalid_rows == 0
    assert len(dataset) == 1
    assert dataset[0].action == "NONE"


def test_aggregate_turn_dataset_multi_turn_commit_continuity_fields_preserved() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "who am i?"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.1,
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.1,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.1,
        },
        {
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"required": False, "reason": "none"},
            "resolved_obligations": ["repair_state_not_required"],
            "confirmed_user_facts": ["name=Sam"],
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["name-fact-initial"],
            "basis_statement": "turn one committed memory fact",
        },
        {"event": "user_utterance_ingest", "utterance": "what name did you commit?"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.05,
            "user_followup_signal_proxy": 0.05,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.05,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.05,
        },
        {
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"required": False, "reason": "none"},
            "resolved_obligations": ["repair_state_not_required"],
            "confirmed_user_facts": ["name=Sam"],
            "retrieval_continuity_evidence": ["commit.confirmed_user_facts:name=Sam"],
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["name-fact-continuity"],
            "basis_statement": "turn two used committed continuity anchor",
        },
    ]

    normalized_rows, summary = aggregator.normalize_and_validate_rows(rows)
    dataset = aggregator.aggregate_turn_dataset(normalized_rows)

    assert summary.invalid_rows == 0
    commit_rows = [row for row in normalized_rows if row.get("event") == "commit_stage_recorded"]
    assert len(commit_rows) == 2
    assert commit_rows[1]["retrieval_continuity_evidence"] == ["commit.confirmed_user_facts:name=Sam"]
    assert len(dataset) == 2
    assert [turn.intent for turn in dataset] == ["memory_recall", "memory_recall"]
    assert [turn.action for turn in dataset] == ["NONE", "NONE"]
    assert [turn.provenance_completeness for turn in dataset] == [1.0, 1.0]


def test_normalize_and_validate_rows_preserves_commit_audit_payload_completeness() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "continue repair"},
        {
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"required": True, "reason": "decision_requires_repair"},
            "resolved_obligations": [],
            "remaining_obligations": ["continue_repair_reconstruction"],
            "confirmed_user_facts": ["name=Sam"],
            "retrieval_continuity_evidence": [
                "commit.pending_repair_state:required",
                "commit.remaining_obligations:continue_repair_reconstruction",
            ],
        },
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.4,
            "user_followup_signal_proxy": 0.4,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.4,
            "chosen_action": "CONTINUE_REPAIR_RECONSTRUCTION",
            "user_followup_signal_proxy": 0.8,
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["repair-anchor-1"],
            "basis_statement": "continuing committed repair from prior turn",
        },
    ]

    normalized_rows, summary = aggregator.normalize_and_validate_rows(rows)
    commit_row = next(row for row in normalized_rows if row.get("event") == "commit_stage_recorded")

    assert summary.invalid_rows == 0
    assert commit_row["pending_repair_state"] == {"required": True, "reason": "decision_requires_repair"}
    assert commit_row["resolved_obligations"] == []
    assert commit_row["remaining_obligations"] == ["continue_repair_reconstruction"]
    assert commit_row["confirmed_user_facts"] == ["name=Sam"]
    assert commit_row["retrieval_continuity_evidence"] == [
        "commit.pending_repair_state:required",
        "commit.remaining_obligations:continue_repair_reconstruction",
    ]

    dataset = aggregator.aggregate_turn_dataset(normalized_rows)
    assert len(dataset) == 1
    assert dataset[0].action == "CONTINUE_REPAIR_RECONSTRUCTION"
    assert dataset[0].provenance_completeness == 1.0
