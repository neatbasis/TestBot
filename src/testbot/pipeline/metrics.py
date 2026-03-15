from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from testbot.canonical_turn_orchestrator import CanonicalTurnOrchestrator

CANONICAL_STAGE_IDS: tuple[str, ...] = CanonicalTurnOrchestrator.STAGE_ORDER
ValidationFailureReason = str


_LATENCY_BUCKETS_MS: tuple[tuple[str, float], ...] = (
    ("lt_10ms", 10.0),
    ("10_to_50ms", 50.0),
    ("50_to_200ms", 200.0),
    ("gte_200ms", float("inf")),
)


def _latency_bucket(latency_ms: float) -> str:
    bounded_latency = max(0.0, float(latency_ms))
    for label, upper_bound in _LATENCY_BUCKETS_MS:
        if bounded_latency < upper_bound:
            return label
    return "gte_200ms"


@dataclass(frozen=True)
class TurnMetricsRecord:
    """Structured per-turn metrics record emitted by the canonical pipeline."""

    turn_id: str
    stage_ids: tuple[str, ...]
    stage_latencies_ms: dict[str, float]
    intent_resolution_confidence: float
    retrieval_branch: str
    retrieval_hits: int
    validation_failure_reasons: tuple[ValidationFailureReason, ...] = ()
    decision_class: str = ""
    hazard_path: bool = False
    interrupted: bool = False

    @property
    def fallback(self) -> bool:
        return self.decision_class == "SAFE_FALLBACK"

    @property
    def retrieval_hit(self) -> bool:
        return self.retrieval_hits > 0

    @property
    def stage_latency_buckets(self) -> dict[str, str]:
        return {stage_id: _latency_bucket(latency_ms) for stage_id, latency_ms in self.stage_latencies_ms.items()}

    @classmethod
    def from_run(
        cls,
        *,
        turn_id: str,
        stage_ids: Iterable[str],
        stage_latencies_ms: dict[str, float],
        intent_resolution_confidence: float,
        retrieval_branch: str,
        retrieval_hits: int,
        validation_failure_reasons: Iterable[ValidationFailureReason] | None = None,
        decision_class: str = "",
        hazard_path: bool = False,
        interrupted: bool = False,
    ) -> TurnMetricsRecord:
        normalized_stage_ids = tuple(stage_ids)
        if normalized_stage_ids != CANONICAL_STAGE_IDS:
            raise ValueError(
                "Pipeline run stage identifiers must exactly match canonical stage order "
                f"{CANONICAL_STAGE_IDS}; got {normalized_stage_ids}."
            )

        missing_stage_latency = [stage_id for stage_id in normalized_stage_ids if stage_id not in stage_latencies_ms]
        if missing_stage_latency:
            raise ValueError(
                "Pipeline run stage latencies must include each canonical stage id; "
                f"missing {missing_stage_latency}."
            )

        extra_stage_latency = sorted(set(stage_latencies_ms).difference(normalized_stage_ids))
        if extra_stage_latency:
            raise ValueError(
                "Pipeline run stage latencies include non-canonical stage ids; "
                f"unexpected {extra_stage_latency}."
            )

        return cls(
            turn_id=turn_id,
            stage_ids=normalized_stage_ids,
            stage_latencies_ms={stage_id: float(stage_latencies_ms[stage_id]) for stage_id in normalized_stage_ids},
            intent_resolution_confidence=float(intent_resolution_confidence),
            retrieval_branch=str(retrieval_branch),
            retrieval_hits=max(0, int(retrieval_hits)),
            validation_failure_reasons=tuple(validation_failure_reasons or ()),
            decision_class=str(decision_class),
            hazard_path=bool(hazard_path),
            interrupted=bool(interrupted),
        )


@dataclass
class PipelineMetrics:
    """Aggregate metrics produced from canonical per-turn metric records."""

    records: list[TurnMetricsRecord] = field(default_factory=list)

    def add_record(self, record: TurnMetricsRecord) -> None:
        self.records.append(record)

    def to_summary(self) -> dict[str, object]:
        stage_latency_buckets: dict[str, dict[str, int]] = {
            stage_id: {label: 0 for label, _ in _LATENCY_BUCKETS_MS} for stage_id in CANONICAL_STAGE_IDS
        }
        confidence_distribution = {
            "lt_0_4": 0,
            "0_4_to_0_7": 0,
            "gte_0_7": 0,
        }
        retrieval_hit_rate_by_branch: dict[str, dict[str, float | int]] = {}
        validation_failure_reasons: dict[str, int] = {}
        fallback_count = 0
        hazard_paths = 0
        hazard_interrupts = 0

        for record in self.records:
            for stage_id, bucket in record.stage_latency_buckets.items():
                stage_latency_buckets[stage_id][bucket] += 1

            confidence = record.intent_resolution_confidence
            if confidence < 0.4:
                confidence_distribution["lt_0_4"] += 1
            elif confidence < 0.7:
                confidence_distribution["0_4_to_0_7"] += 1
            else:
                confidence_distribution["gte_0_7"] += 1

            branch_entry = retrieval_hit_rate_by_branch.setdefault(
                record.retrieval_branch,
                {"turns": 0, "hits": 0, "hit_rate": 0.0},
            )
            branch_entry["turns"] += 1
            if record.retrieval_hit:
                branch_entry["hits"] += 1

            for reason in record.validation_failure_reasons:
                validation_failure_reasons[reason] = validation_failure_reasons.get(reason, 0) + 1

            if record.fallback:
                fallback_count += 1
            if record.hazard_path:
                hazard_paths += 1
                if record.interrupted:
                    hazard_interrupts += 1

        for branch_entry in retrieval_hit_rate_by_branch.values():
            turns = int(branch_entry["turns"])
            hits = int(branch_entry["hits"])
            branch_entry["hit_rate"] = (hits / turns) if turns else 0.0

        total_turns = len(self.records)
        return {
            "turn_count": total_turns,
            "stage_latency_buckets": stage_latency_buckets,
            "intent_resolution_confidence_distribution": confidence_distribution,
            "retrieval_hit_rate_by_branch": retrieval_hit_rate_by_branch,
            "validation_failure_reasons": validation_failure_reasons,
            "fallback_rate": (fallback_count / total_turns) if total_turns else 0.0,
            "fallback_count": fallback_count,
            "hazard_interrupt_rate": (hazard_interrupts / hazard_paths) if hazard_paths else 0.0,
            "hazard_paths": hazard_paths,
            "hazard_interrupts": hazard_interrupts,
        }
