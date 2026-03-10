from __future__ import annotations

from dataclasses import dataclass, replace

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


def commit_answer_stage(
    state: PipelineState,
    *,
    assembly: AnswerCandidate,
    validation: ValidatedAnswer,
    rendered: RenderedAnswer,
    commit_stage_id: str = "answer.commit",
) -> tuple[PipelineState, CommittedTurnState]:
    if not validation.passed:
        raise ValueError("cannot commit answer before validation boundary passes")

    committed_facts = _merge_confirmed_user_facts(assembly=assembly, state=state)

    commit_receipt = CommitReceiptArtifact.from_mapping(
        {
            "committed": True,
            "commit_id": commit_stage_id,
            "commit_stage": commit_stage_id,
            "pipeline_state_snapshot": "recorded",
            "pending_repair_state": assembly.pending_repair_state,
            "pending_ingestion_request_id": assembly.pending_ingestion_request_id,
            "resolved_obligations": list(assembly.resolved_obligations),
            "remaining_obligations": list(assembly.remaining_obligations),
            "confirmed_user_facts": committed_facts,
        }
    )
    turn_id = str(state.candidate_facts.get("turn_id") or state.commit_receipt.get("turn_id") or "")
    committed_turn_state = CommittedTurnState(
        turn_id=turn_id,
        commit_stage=commit_stage_id,
        rendered_text=rendered.rendered_text,
        pending_repair_state=dict(assembly.pending_repair_state),
        pending_ingestion_request_id=assembly.pending_ingestion_request_id,
        resolved_obligations=list(assembly.resolved_obligations),
        remaining_obligations=list(assembly.remaining_obligations),
        confirmed_user_facts=committed_facts,
    )
    return (
        replace(
            state,
            final_answer=rendered.rendered_text,
            claims=list(validation.claims or []),
            provenance_types=list(validation.provenance_types or []),
            used_memory_refs=list(validation.used_memory_refs or []),
            used_source_evidence_refs=list(validation.used_source_evidence_refs or []),
            source_evidence_attribution=list(validation.source_evidence_attribution or []),
            basis_statement=validation.basis_statement,
            invariant_decisions=dict(validation.invariant_decisions or {}),
            alignment_decision=dict(validation.alignment_decision or {}),
            pending_repair=assembly.pending_repair_state,
            commit_receipt=commit_receipt,
        ),
        committed_turn_state,
    )
