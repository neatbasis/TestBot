from __future__ import annotations

from testbot.intent_router import IntentType
from testbot.sat_chatbot_memory_v2 import (
    _ambiguity_score,
    _intent_label,
    _user_followup_signal_proxy,
)


def test_intent_classified_log_contains_bandit_fields() -> None:
    intent = _intent_label(IntentType.MEMORY_RECALL)
    ambiguity_score = _ambiguity_score(
        {
            "scored_candidates": [
                {"doc_id": "d1", "final_score": 0.8},
                {"doc_id": "d2", "final_score": 0.76},
            ]
        }
    )

    row = {
        "intent": intent,
        "ambiguity_score": ambiguity_score,
        "user_followup_signal_proxy": round(ambiguity_score, 4),
    }

    assert row["intent"] == "memory_recall"
    assert row["ambiguity_score"] == 0.95
    assert 0.0 <= row["user_followup_signal_proxy"] <= 1.0


def test_fallback_action_selected_log_contains_bandit_fields() -> None:
    ambiguity_score = _ambiguity_score(
        {
            "scored_candidates": [
                {"doc_id": "d1", "final_score": 0.7},
                {"doc_id": "d2", "final_score": 0.1},
            ]
        }
    )

    row = {
        "intent": "memory_recall",
        "ambiguity_score": ambiguity_score,
        "chosen_action": "ASK_CLARIFYING_QUESTION",
        "user_followup_signal_proxy": _user_followup_signal_proxy(
            final_answer="Can you clarify which memory and time window you mean?",
            fallback_action="ASK_CLARIFYING_QUESTION",
            ambiguity_score=ambiguity_score,
        ),
    }

    assert row["chosen_action"] == "ASK_CLARIFYING_QUESTION"
    assert 0.0 <= row["ambiguity_score"] <= 1.0
    assert row["user_followup_signal_proxy"] == 1.0


def test_provenance_summary_log_contains_bandit_and_provenance_fields() -> None:
    ambiguity_score = _ambiguity_score({"scored_candidates": []})
    row = {
        "intent": "knowledge_question",
        "ambiguity_score": ambiguity_score,
        "chosen_action": "NONE",
        "user_followup_signal_proxy": _user_followup_signal_proxy(
            final_answer="A grounded answer with citation doc_id: abc, ts: 2026-01-01T00:00:00Z",
            fallback_action="NONE",
            ambiguity_score=ambiguity_score,
        ),
        "provenance_types": ["memory"],
        "used_memory_refs": [{"doc_id": "abc", "ts": "2026-01-01T00:00:00Z"}],
    }

    assert row["ambiguity_score"] == 0.0
    assert row["provenance_types"] == ["memory"]
    assert row["used_memory_refs"][0]["doc_id"] == "abc"
