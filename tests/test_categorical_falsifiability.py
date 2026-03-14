from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_RELEASE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aggregate_turn_analytics.py"
_spec = importlib.util.spec_from_file_location("aggregate_turn_analytics", _RELEASE_PATH)
assert _spec and _spec.loader
aggregator = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aggregator
_spec.loader.exec_module(aggregator)


def test_evaluate_categorical_falsifiability_passes_when_log_witnesses_exist() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "continue repair"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.4,
            "user_followup_signal_proxy": 0.5,
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
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"repair_required_by_policy": True, "repair_offered_to_user": True},
            "remaining_obligations": ["continue_repair_reconstruction"],
            "retrieval_continuity_evidence": ["commit.pending_repair_state:repair_offered_to_user"],
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["repair-anchor-1"],
            "basis_statement": "continuation grounded in committed repair anchor",
        },
    ]

    summary = aggregator.evaluate_categorical_falsifiability(rows)

    assert summary["pass"] is True
    assert summary["violations"] == []
    assert summary["checks"] == {
        "local_repair_confinement": True,
        "justified_transport": True,
        "reindexing_coherence": True,
    }
    assert summary["observed_case_counts"] == {
        "local_repair_confinement": 1,
        "justified_transport": 1,
        "reindexing_coherence": 1,
    }
    assert summary["vacuous_checks"] == []


def test_evaluate_categorical_falsifiability_reports_minimal_violation_set() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "continue"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.3,
            "user_followup_signal_proxy": 0.3,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "knowledge_question",
            "ambiguity_score": 0.3,
            "chosen_action": "CONTINUE_REPAIR_RECONSTRUCTION",
            "user_followup_signal_proxy": 0.7,
        },
        {
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"repair_required_by_policy": False, "repair_offered_to_user": False},
            "remaining_obligations": [],
            "retrieval_continuity_evidence": ["commit.confirmed_user_facts:name=Sam"],
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": [],
            "basis_statement": "",
        },
    ]

    summary = aggregator.evaluate_categorical_falsifiability(rows)

    assert summary["pass"] is False
    assert summary["checked_turn_count"] == 1
    assert {item["law"] for item in summary["violations"]} == {
        "local_repair_confinement",
        "justified_transport",
        "reindexing_coherence",
    }



def test_evaluate_categorical_falsifiability_marks_vacuous_checks_on_non_repair_fixture() -> None:
    rows = [
        {"event": "user_utterance_ingest", "utterance": "What did I say yesterday?"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.2,
            "user_followup_signal_proxy": 0.2,
        },
        {
            "event": "fallback_action_selected",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.2,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.2,
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": [{"doc_id": "d1"}],
            "basis_statement": "derived from memory",
        },
    ]

    summary = aggregator.evaluate_categorical_falsifiability(rows)

    assert summary["pass"] is True
    assert summary["checked_turn_count"] == 1
    assert summary["observed_case_counts"] == {
        "local_repair_confinement": 0,
        "justified_transport": 0,
        "reindexing_coherence": 1,
    }
    assert set(summary["vacuous_checks"]) == {"local_repair_confinement", "justified_transport"}


def test_evaluate_categorical_falsifiability_detects_justified_transport_regression_from_single_field_drop() -> None:
    base_rows = [
        {"event": "user_utterance_ingest", "utterance": "continue repair"},
        {
            "event": "intent_classified",
            "schema_version": 3,
            "intent": "memory_recall",
            "ambiguity_score": 0.4,
            "user_followup_signal_proxy": 0.5,
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
            "event": "commit_stage_recorded",
            "schema_version": 3,
            "stage": "answer.commit",
            "pending_repair_state": {"repair_required_by_policy": True, "repair_offered_to_user": True},
            "remaining_obligations": ["continue_repair_reconstruction"],
            "retrieval_continuity_evidence": ["commit.pending_repair_state:repair_offered_to_user"],
        },
        {
            "event": "provenance_summary",
            "schema_version": 3,
            "provenance_types": ["MEMORY"],
            "used_memory_refs": ["repair-anchor-1"],
            "basis_statement": "continuation grounded in committed repair anchor",
        },
    ]

    regressed_rows = list(base_rows)
    regressed_rows[-1] = {
        **regressed_rows[-1],
        "basis_statement": "",
    }

    summary = aggregator.evaluate_categorical_falsifiability(regressed_rows)

    assert summary["pass"] is False
    assert [item["law"] for item in summary["violations"]] == ["justified_transport"]
