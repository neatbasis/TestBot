from __future__ import annotations

import pytest

from testbot.pipeline.metrics import CANONICAL_STAGE_IDS, PipelineMetrics, TurnMetricsRecord


def _stage_latencies(default_ms: float = 9.0, **overrides: float) -> dict[str, float]:
    latencies = {stage_id: default_ms for stage_id in CANONICAL_STAGE_IDS}
    latencies.update(overrides)
    return latencies


def _record(
    turn_id: str,
    *,
    intent_resolution_confidence: float,
    retrieval_branch: str,
    retrieval_hits: int,
    validation_failure_reasons: tuple[str, ...] = (),
    decision_class: str = "ANSWER_FROM_MEMORY",
    hazard_path: bool = False,
    interrupted: bool = False,
    stage_latencies_ms: dict[str, float] | None = None,
) -> TurnMetricsRecord:
    return TurnMetricsRecord.from_run(
        turn_id=turn_id,
        stage_ids=CANONICAL_STAGE_IDS,
        stage_latencies_ms=stage_latencies_ms or _stage_latencies(),
        intent_resolution_confidence=intent_resolution_confidence,
        retrieval_branch=retrieval_branch,
        retrieval_hits=retrieval_hits,
        validation_failure_reasons=validation_failure_reasons,
        decision_class=decision_class,
        hazard_path=hazard_path,
        interrupted=interrupted,
    )


def test_turn_metrics_record_requires_canonical_stage_identifiers_in_order() -> None:
    with pytest.raises(ValueError, match="must exactly match canonical stage order"):
        TurnMetricsRecord.from_run(
            turn_id="turn-1",
            stage_ids=tuple(reversed(CANONICAL_STAGE_IDS)),
            stage_latencies_ms=_stage_latencies(),
            intent_resolution_confidence=0.9,
            retrieval_branch="memory",
            retrieval_hits=1,
        )


def test_stage_latency_buckets_are_counted_per_canonical_stage() -> None:
    metrics = PipelineMetrics()
    metrics.add_record(
        _record(
            "turn-1",
            intent_resolution_confidence=0.8,
            retrieval_branch="memory",
            retrieval_hits=1,
            stage_latencies_ms=_stage_latencies(
                **{
                    "observe.turn": 5.0,
                    "encode.candidates": 25.0,
                    "intent.resolve": 180.0,
                    "answer.commit": 350.0,
                }
            ),
        )
    )

    summary = metrics.to_summary()

    assert summary["stage_latency_buckets"]["observe.turn"]["lt_10ms"] == 1
    assert summary["stage_latency_buckets"]["encode.candidates"]["10_to_50ms"] == 1
    assert summary["stage_latency_buckets"]["intent.resolve"]["50_to_200ms"] == 1
    assert summary["stage_latency_buckets"]["answer.commit"]["gte_200ms"] == 1


def test_intent_confidence_distribution_retrieval_hit_rate_and_validation_failures() -> None:
    metrics = PipelineMetrics()
    metrics.add_record(
        _record(
            "turn-1",
            intent_resolution_confidence=0.2,
            retrieval_branch="memory",
            retrieval_hits=1,
            validation_failure_reasons=("missing_provenance",),
        )
    )
    metrics.add_record(
        _record(
            "turn-2",
            intent_resolution_confidence=0.5,
            retrieval_branch="memory",
            retrieval_hits=0,
            validation_failure_reasons=("missing_provenance", "class_mismatch"),
            decision_class="SAFE_FALLBACK",
        )
    )
    metrics.add_record(
        _record(
            "turn-3",
            intent_resolution_confidence=0.85,
            retrieval_branch="source",
            retrieval_hits=0,
            hazard_path=True,
            interrupted=True,
        )
    )

    summary = metrics.to_summary()

    assert summary["intent_resolution_confidence_distribution"] == {
        "lt_0_4": 1,
        "0_4_to_0_7": 1,
        "gte_0_7": 1,
    }

    assert summary["retrieval_hit_rate_by_branch"] == {
        "memory": {"turns": 2, "hits": 1, "hit_rate": 0.5},
        "source": {"turns": 1, "hits": 0, "hit_rate": 0.0},
    }

    assert summary["validation_failure_reasons"] == {
        "missing_provenance": 2,
        "class_mismatch": 1,
    }

    assert summary["fallback_count"] == 1
    assert summary["fallback_rate"] == pytest.approx(1 / 3)
    assert summary["hazard_paths"] == 1
    assert summary["hazard_interrupts"] == 1
    assert summary["hazard_interrupt_rate"] == 1.0
