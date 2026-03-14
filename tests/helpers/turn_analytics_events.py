from __future__ import annotations

from typing import Any


def build_grounded_memory_and_fallback_turn_rows() -> list[dict[str, Any]]:
    """Return a deterministic two-turn sequence for turn analytics aggregation."""
    return [
        {
            "ts": "2026-01-01T00:00:00Z",
            "event": "user_utterance_ingest",
            "utterance": "What did I say yesterday?",
        },
        {
            "ts": "2026-01-01T00:00:01Z",
            "event": "intent_classified",
            "intent": "memory_recall",
            "ambiguity_score": 0.2,
            "user_followup_signal_proxy": 0.2,
        },
        {
            "ts": "2026-01-01T00:00:02Z",
            "event": "fallback_action_selected",
            "intent": "memory_recall",
            "ambiguity_score": 0.2,
            "chosen_action": "NONE",
            "user_followup_signal_proxy": 0.2,
        },
        {
            "ts": "2026-01-01T00:00:03Z",
            "event": "provenance_summary",
            "provenance_types": ["memory"],
            "used_memory_refs": [{"doc_id": "d1"}],
            "used_source_evidence_refs": ["src-1"],
            "source_evidence_attribution": [
                {
                    "doc_id": "src-1",
                    "source_type": "calendar",
                    "source_uri": "calendar://work/evt-1",
                    "retrieved_at": "2026-01-01T00:00:03Z",
                    "trust_tier": "high",
                }
            ],
            "basis_statement": "derived from memory",
        },
        {
            "ts": "2026-01-01T00:00:04Z",
            "event": "user_utterance_ingest",
            "utterance": "What is my SSN?",
        },
        {
            "ts": "2026-01-01T00:00:05Z",
            "event": "intent_classified",
            "intent": "knowledge_question",
            "ambiguity_score": 0.9,
            "user_followup_signal_proxy": 0.9,
        },
        {
            "ts": "2026-01-01T00:00:06Z",
            "event": "fallback_action_selected",
            "intent": "knowledge_question",
            "ambiguity_score": 0.9,
            "chosen_action": "ASK_CLARIFYING_QUESTION",
            "user_followup_signal_proxy": 1.0,
        },
        {
            "ts": "2026-01-01T00:00:07Z",
            "event": "provenance_summary",
            "provenance_types": [],
            "used_memory_refs": [],
            "used_source_evidence_refs": [],
            "source_evidence_attribution": [],
            "basis_statement": "",
        },
    ]


def build_dashboard_safe_alignment_dimension_rows() -> list[dict[str, Any]]:
    """Return mixed numeric/not_applicable alignment rows for summary checks."""
    return [
        {
            "event": "alignment_decision_evaluated",
            "alignment_dimensions": {
                "factual_grounding_reliability": 0.95,
                "response_utility": 0.9,
                "cost_latency_budget": 0.88,
            },
        },
        {
            "event": "alignment_decision_evaluated",
            "alignment_dimensions": {
                "factual_grounding_reliability": "not_applicable",
                "response_utility": 0.65,
                "cost_latency_budget": 0.9,
            },
        },
    ]

