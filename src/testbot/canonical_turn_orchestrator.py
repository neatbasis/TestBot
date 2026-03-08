from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from testbot.pipeline_state import PipelineState


StageResult = TypeVar("StageResult")


@dataclass
class CanonicalTurnContext:
    """Mutable per-turn context passed across canonical stages."""

    state: PipelineState
    stage_audit_trail: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalStage:
    name: str
    handler: Callable[[CanonicalTurnContext], CanonicalTurnContext]


class CanonicalTurnOrchestrator:
    """Explicit, auditable canonical 11-stage turn pipeline executor."""

    STAGE_ORDER: tuple[str, ...] = (
        "observe.turn",
        "encode.candidates",
        "stabilize.pre_route",
        "context.resolve",
        "intent.resolve",
        "retrieve.evidence",
        "policy.decide",
        "answer.assemble",
        "answer.validate",
        "answer.render",
        "answer.commit",
    )

    def __init__(self, stages: list[CanonicalStage]) -> None:
        stage_names = tuple(stage.name for stage in stages)
        if stage_names != self.STAGE_ORDER:
            raise ValueError(
                "Canonical stages must exactly match the required order "
                f"{self.STAGE_ORDER}, got {stage_names}."
            )
        self._stages = stages

    def run(self, context: CanonicalTurnContext) -> CanonicalTurnContext:
        for expected_stage, stage in zip(self.STAGE_ORDER, self._stages):
            if expected_stage == "intent.resolve":
                if "turn_observation" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires turn_observation artifact")
                if "encoded_candidates" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires encoded_candidates artifact")
                if "stabilized_turn_state" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires stabilized_turn_state artifact")
            if expected_stage == "policy.decide":
                if "stabilized_turn_state" not in context.artifacts:
                    raise RuntimeError("policy.decide requires stabilized_turn_state artifact")
                if "retrieval_result" not in context.artifacts:
                    raise RuntimeError("policy.decide requires retrieval_result artifact")
            if stage.name != expected_stage:
                raise RuntimeError(
                    f"Stage order violation: expected {expected_stage}, got {stage.name}."
                )
            context = stage.handler(context)
            context.stage_audit_trail.append(stage.name)
        return context
