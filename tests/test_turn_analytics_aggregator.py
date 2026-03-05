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
