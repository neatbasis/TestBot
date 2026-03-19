from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.pipeline_state import AlignmentDecision, CommitReceiptArtifact, InvariantDecision, PipelineState


@dataclass(frozen=True)
class PendingRepairState:
    repair_required_by_policy: bool = False
    repair_offered_to_user: bool = False
    offer_type: str = ""
    reason: str = "none"
    followup_route: str = ""
    obligation_id: str = ""

    def as_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "repair_required_by_policy": self.repair_required_by_policy,
            "repair_offered_to_user": self.repair_offered_to_user,
            "reason": self.reason,
        }
        if self.offer_type:
            payload["offer_type"] = self.offer_type
        if self.followup_route:
            payload["followup_route"] = self.followup_route
        if self.obligation_id:
            payload["obligation_id"] = self.obligation_id
        return payload

    def get(self, key: str, default: object = None) -> object:
        return self.as_mapping().get(key, default)

    def __getitem__(self, key: str) -> object:
        return self.as_mapping()[key]


@dataclass(frozen=True)
class CommittedTurnState:
    turn_id: str
    commit_stage: str
    rendered_text: str
    pending_repair_state: PendingRepairState | dict[str, object]
    pending_ingestion_request_id: str
    resolved_obligations: list[str]
    remaining_obligations: list[str]
    confirmed_user_facts: list[str]

    def __post_init__(self) -> None:
        if isinstance(self.pending_repair_state, dict):
            object.__setattr__(self, "pending_repair_state", PendingRepairState(**{
                "repair_required_by_policy": bool(self.pending_repair_state.get("repair_required_by_policy", False)),
                "repair_offered_to_user": bool(self.pending_repair_state.get("repair_offered_to_user", False)),
                "offer_type": str(self.pending_repair_state.get("offer_type") or ""),
                "reason": str(self.pending_repair_state.get("reason") or "none"),
                "followup_route": str(self.pending_repair_state.get("followup_route") or ""),
                "obligation_id": str(self.pending_repair_state.get("obligation_id") or ""),
            }))


@dataclass(frozen=True)
class CommitValidationPayload:
    passed: bool
    claims: list[str]
    provenance_types: list[object]
    used_memory_refs: list[str]
    used_source_evidence_refs: list[str]
    source_evidence_attribution: list[dict[str, object]]
    basis_statement: str
    invariant_decisions: InvariantDecision
    alignment_decision: AlignmentDecision


@dataclass(frozen=True)
class CommitRenderingPayload:
    rendered_text: str
    response_contract: str
    degraded_response: bool
    repair_offer_rendered: bool
    repair_followup_route: str


@dataclass(frozen=True)
class CommitStageInputs:
    validation: CommitValidationPayload
    rendering: CommitRenderingPayload


def _merge_confirmed_user_facts(*, assembly: AnswerCandidate, state: PipelineState) -> list[str]:
    del state
    return list(dict.fromkeys(str(fact).strip() for fact in assembly.confirmed_user_facts if str(fact).strip()))


def build_commit_stage_inputs(
    *,
    validation: ValidatedAnswer,
    rendered: RenderedAnswer,
) -> CommitStageInputs:
    return CommitStageInputs(
        validation=CommitValidationPayload(
            passed=validation.passed,
            claims=list(validation.claims or []),
            provenance_types=list(validation.provenance_types or []),
            used_memory_refs=list(validation.used_memory_refs or []),
            used_source_evidence_refs=list(validation.used_source_evidence_refs or []),
            source_evidence_attribution=list(validation.source_evidence_attribution or []),
            basis_statement=validation.basis_statement,
            invariant_decisions=InvariantDecision.from_mapping(validation.invariant_decisions),
            alignment_decision=AlignmentDecision.from_mapping(validation.alignment_decision),
        ),
        rendering=CommitRenderingPayload(
            rendered_text=rendered.rendered_text,
            response_contract=str(getattr(rendered, "response_contract", "validated_normal") or "validated_normal"),
            degraded_response=bool(getattr(rendered, "degraded_response", False)),
            repair_offer_rendered=bool(getattr(rendered, "repair_offer_rendered", False)),
            repair_followup_route=str(getattr(rendered, "repair_followup_route", "") or "repair_offer_followup"),
        ),
    )


@dataclass(frozen=True)
class AnswerCommitService:
    merge_confirmed_user_facts: Callable[..., list[str]] = _merge_confirmed_user_facts

    def commit(
        self,
        state: PipelineState,
        *,
        assembly: AnswerCandidate,
        commit_inputs: CommitStageInputs,
        commit_stage_id: str = "answer.commit",
    ) -> tuple[PipelineState, CommittedTurnState]:
        degraded_response = commit_inputs.rendering.degraded_response
        if not commit_inputs.validation.passed and not degraded_response:
            raise ValueError("cannot commit failed-validation answer unless rendered artifact is explicitly degraded")

        if commit_inputs.validation.passed and degraded_response:
            raise ValueError("validated answers must not be committed through degraded response contract")

        committed_facts = self.merge_confirmed_user_facts(assembly=assembly, state=state)

        turn_id = str(state.candidate_facts.turn_id or state.commit_receipt.continuity_turn_id or "")
        repair_offer_rendered = commit_inputs.rendering.repair_offer_rendered
        pending_repair_state = PendingRepairState(
            repair_required_by_policy=assembly.pending_repair_state.repair_required_by_policy,
            repair_offered_to_user=repair_offer_rendered,
            offer_type=assembly.pending_repair_state.offer_type,
            reason=assembly.pending_repair_state.reason,
            followup_route=assembly.pending_repair_state.followup_route,
            obligation_id=f"{commit_stage_id}:{turn_id}:pending_repair",
        )
        if repair_offer_rendered:
            pending_repair_state = replace(
                pending_repair_state,
                reason="repair_offer_rendered",
                followup_route=commit_inputs.rendering.repair_followup_route,
            )
        else:
            pending_repair_state = replace(
                pending_repair_state,
                reason="none",
                offer_type="",
                followup_route="",
            )

        commit_receipt = CommitReceiptArtifact.from_mapping(
            {
                "committed": True,
                "commit_id": commit_stage_id,
                "commit_stage": commit_stage_id,
                "turn_id": turn_id,
                "pipeline_state_snapshot": "recorded",
                "pending_repair_state": pending_repair_state.as_mapping(),
                "pending_ingestion_request_id": assembly.pending_ingestion_request_id,
                "resolved_obligations": list(assembly.resolved_obligations),
                "remaining_obligations": list(assembly.remaining_obligations),
                "confirmed_user_facts": committed_facts,
                "response_contract": commit_inputs.rendering.response_contract,
                "degraded_response": degraded_response,
            }
        )
        committed_turn_state = CommittedTurnState(
            turn_id=turn_id,
            commit_stage=commit_stage_id,
            rendered_text=commit_inputs.rendering.rendered_text,
            pending_repair_state=pending_repair_state,
            pending_ingestion_request_id=assembly.pending_ingestion_request_id,
            resolved_obligations=list(assembly.resolved_obligations),
            remaining_obligations=list(assembly.remaining_obligations),
            confirmed_user_facts=committed_facts,
        )
        return (
            replace(
                state,
                final_answer=commit_inputs.rendering.rendered_text,
                claims=commit_inputs.validation.claims,
                provenance_types=commit_inputs.validation.provenance_types,
                used_memory_refs=commit_inputs.validation.used_memory_refs,
                used_source_evidence_refs=commit_inputs.validation.used_source_evidence_refs,
                source_evidence_attribution=commit_inputs.validation.source_evidence_attribution,
                basis_statement=commit_inputs.validation.basis_statement,
                invariant_decisions=commit_inputs.validation.invariant_decisions,
                alignment_decision=commit_inputs.validation.alignment_decision,
                pending_repair=(pending_repair_state.as_mapping() if repair_offer_rendered else {}),
                commit_receipt=commit_receipt,
            ),
            committed_turn_state,
        )


def commit_answer_stage(
    state: PipelineState,
    *,
    assembly: AnswerCandidate,
    validation: ValidatedAnswer,
    rendered: RenderedAnswer,
    commit_stage_id: str = "answer.commit",
) -> tuple[PipelineState, CommittedTurnState]:
    commit_inputs = build_commit_stage_inputs(validation=validation, rendered=rendered)
    return AnswerCommitService().commit(
        state,
        assembly=assembly,
        commit_inputs=commit_inputs,
        commit_stage_id=commit_stage_id,
    )
