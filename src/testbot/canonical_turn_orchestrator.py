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
        semantic_contracts: dict[str, Any] = {}

        for expected_stage, stage in zip(self.STAGE_ORDER, self._stages):
            if expected_stage == "answer.validate":
                semantic_contracts["pre_validation_answer_assembly_fingerprint"] = self._artifact_fingerprint(
                    context.artifacts.get("answer_assembly_contract")
                )
            if expected_stage == "intent.resolve":
                if "turn_observation" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires turn_observation artifact")
                if "encoded_candidates" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires encoded_candidates artifact")
                if "stabilized_turn_state" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires stabilized_turn_state artifact")
                if "resolved_context" not in context.artifacts:
                    raise RuntimeError("intent.resolve requires resolved_context artifact")
                if "resolved_context_fingerprint" not in semantic_contracts:
                    raise RuntimeError(
                        "intent.resolve requires context.resolve to establish resolved_context contract"
                    )
                if self._artifact_fingerprint(
                    context.artifacts["resolved_context"]
                ) != semantic_contracts.get("resolved_context_fingerprint"):
                    raise RuntimeError("intent.resolve detected resolved_context contract drift")
            if expected_stage == "policy.decide":
                if "stabilized_turn_state" not in context.artifacts:
                    raise RuntimeError("policy.decide requires stabilized_turn_state artifact")
                if "retrieval_result" not in context.artifacts:
                    raise RuntimeError("policy.decide requires retrieval_result artifact")
                if "stabilized_turn_state_fingerprint" not in semantic_contracts:
                    raise RuntimeError(
                        "policy.decide requires stabilize.pre_route semantic contract"
                    )
                if self._artifact_fingerprint(
                    context.artifacts["stabilized_turn_state"]
                ) != semantic_contracts.get("stabilized_turn_state_fingerprint"):
                    raise RuntimeError("policy.decide requires unmodified stabilized_turn_state contract")
                if "resolved_context" not in context.artifacts:
                    raise RuntimeError("policy.decide requires resolved_context artifact")
                if not self._retrieval_posture(context.artifacts["retrieval_result"]):
                    raise RuntimeError("policy.decide requires retrieval_result posture semantics")
            if expected_stage == "answer.render":
                if "answer_validation_contract" not in context.artifacts:
                    raise RuntimeError("answer.render requires answer_validation_contract artifact")
                if not getattr(context.artifacts["answer_validation_contract"], "passed", False):
                    raise RuntimeError("answer.render requires a passing answer.validate contract")
                if self._artifact_fingerprint(
                    context.artifacts.get("answer_assembly_contract")
                ) != semantic_contracts.get("validated_answer_assembly_fingerprint"):
                    raise RuntimeError(
                        "answer.render detected class drift between validated and rendered answer assembly"
                    )
            if stage.name != expected_stage:
                raise RuntimeError(
                    f"Stage order violation: expected {expected_stage}, got {stage.name}."
                )
            context = stage.handler(context)
            if expected_stage == "stabilize.pre_route":
                if "stabilized_turn_state" not in context.artifacts:
                    raise RuntimeError("stabilize.pre_route must produce stabilized_turn_state artifact")
                semantic_contracts["stabilized_turn_state_fingerprint"] = self._artifact_fingerprint(
                    context.artifacts["stabilized_turn_state"]
                )
            if expected_stage == "context.resolve":
                if "resolved_context" not in context.artifacts:
                    raise RuntimeError("context.resolve must produce resolved_context artifact")
                semantic_contracts["resolved_context_fingerprint"] = self._artifact_fingerprint(
                    context.artifacts["resolved_context"]
                )
            if expected_stage == "answer.validate":
                if "answer_validation_contract" not in context.artifacts:
                    raise RuntimeError("answer.validate must produce answer_validation_contract artifact")
                semantic_contracts["validated_answer_assembly_fingerprint"] = semantic_contracts.get(
                    "pre_validation_answer_assembly_fingerprint",
                    self._artifact_fingerprint(context.artifacts.get("answer_assembly_contract")),
                )
            context.stage_audit_trail.append(stage.name)
        return context

    @staticmethod
    def _artifact_fingerprint(artifact: Any) -> tuple[str, str]:
        if artifact is None:
            return ("none", "")
        values = getattr(artifact, "__dict__", artifact)
        if not isinstance(values, dict):
            return (type(artifact).__name__, repr(artifact))
        normalized = "|".join(
            f"{key}={repr(values[key])}" for key in sorted(values)
        )
        return (type(artifact).__name__, normalized)

    @staticmethod
    def _retrieval_posture(retrieval_result: Any) -> str:
        if retrieval_result is None:
            return ""
        if isinstance(retrieval_result, dict):
            return str(retrieval_result.get("posture") or retrieval_result.get("evidence_posture") or "")
        posture = getattr(retrieval_result, "evidence_posture", "")
        return str(getattr(posture, "value", posture) or "")
