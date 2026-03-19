from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import ValidatedAnswer
from testbot.pipeline_state import CommitReceiptArtifact, PipelineState


@dataclass(frozen=True)
class CommittedTurnState:
    turn_id: str
    commit_stage: str
    rendered_text: str
    pending_repair_state: dict[str, object]
    pending_ingestion_request_id: str
    resolved_obligations: list[str]
    remaining_obligations: list[str]
    confirmed_user_facts: list[str]


@dataclass(frozen=True)
class CommitValidationPayload:
    passed: bool
    claims: list[str]
    provenance_types: list[object]
    used_memory_refs: list[str]
    used_source_evidence_refs: list[str]
    source_evidence_attribution: list[dict[str, object]]
    basis_statement: str
    invariant_decisions: dict[str, object]
    alignment_decision: dict[str, object]


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


def _normalize_identity_candidate(raw_value: str) -> str:
    collapsed = " ".join(str(raw_value or "").strip().split())
    if not collapsed:
        return ""
    return " ".join(token.capitalize() for token in collapsed.split(" "))


def _extract_stabilized_identity_fact(state: PipelineState) -> str:
    facts = state.candidate_facts.get("facts", [])
    if not isinstance(facts, list):
        return ""

    identity_candidates: list[str] = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        if str(fact.get("key") or "").strip() != "user_name":
            continue
        normalized = _normalize_identity_candidate(str(fact.get("value") or ""))
        if normalized:
            identity_candidates.append(normalized)

    unique_candidates = tuple(dict.fromkeys(identity_candidates))
    if not unique_candidates:
        return ""
    if len(unique_candidates) > 1:
        return ""
    return f"name={unique_candidates[0]}"


def _has_identity_contradiction(confirmed_user_facts: list[str], candidate_identity_fact: str) -> bool:
    if not candidate_identity_fact:
        return False

    prefix = "name="
    candidate_identity = candidate_identity_fact[len(prefix) :]
    for fact in confirmed_user_facts:
        normalized_fact = str(fact).strip()
        if not normalized_fact.startswith(prefix):
            continue
        if normalized_fact[len(prefix) :] != candidate_identity:
            return True
    return False


def _merge_confirmed_user_facts(*, assembly: AnswerCandidate, state: PipelineState) -> list[str]:
    merged = [str(fact).strip() for fact in assembly.confirmed_user_facts if str(fact).strip()]
    stabilized_identity_fact = _extract_stabilized_identity_fact(state)
    if stabilized_identity_fact and not _has_identity_contradiction(merged, stabilized_identity_fact):
        merged.append(stabilized_identity_fact)
    return list(dict.fromkeys(merged))


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
            invariant_decisions=dict(validation.invariant_decisions or {}),
            alignment_decision=dict(validation.alignment_decision or {}),
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

        repair_offer_rendered = commit_inputs.rendering.repair_offer_rendered
        pending_repair_state = {
            **dict(assembly.pending_repair_state),
            "repair_offered_to_user": repair_offer_rendered,
        }
        if repair_offer_rendered:
            pending_repair_state["reason"] = "repair_offer_rendered"
            pending_repair_state["followup_route"] = commit_inputs.rendering.repair_followup_route
        else:
            pending_repair_state["reason"] = "none"
            pending_repair_state.pop("followup_route", None)
            pending_repair_state.pop("offer_type", None)

        commit_receipt = CommitReceiptArtifact.from_mapping(
            {
                "committed": True,
                "commit_id": commit_stage_id,
                "commit_stage": commit_stage_id,
                "pipeline_state_snapshot": "recorded",
                "pending_repair_state": pending_repair_state,
                "pending_ingestion_request_id": assembly.pending_ingestion_request_id,
                "resolved_obligations": list(assembly.resolved_obligations),
                "remaining_obligations": list(assembly.remaining_obligations),
                "confirmed_user_facts": committed_facts,
                "response_contract": commit_inputs.rendering.response_contract,
                "degraded_response": degraded_response,
            }
        )
        turn_id = str(state.candidate_facts.get("turn_id") or state.commit_receipt.get("turn_id") or "")
        committed_turn_state = CommittedTurnState(
            turn_id=turn_id,
            commit_stage=commit_stage_id,
            rendered_text=commit_inputs.rendering.rendered_text,
            pending_repair_state=dict(pending_repair_state),
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
                pending_repair=(pending_repair_state if repair_offer_rendered else {}),
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
