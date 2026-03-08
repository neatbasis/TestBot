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
    resolved_obligations: list[str]
    remaining_obligations: list[str]
    confirmed_user_facts: list[str]


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

    commit_receipt = CommitReceiptArtifact.from_mapping(
        {
            "committed": True,
            "commit_id": commit_stage_id,
            "commit_stage": commit_stage_id,
            "pipeline_state_snapshot": "recorded",
            "pending_repair_state": assembly.pending_repair_state,
            "resolved_obligations": list(assembly.resolved_obligations),
            "remaining_obligations": list(assembly.remaining_obligations),
            "confirmed_user_facts": list(assembly.confirmed_user_facts),
        }
    )
    turn_id = str(state.candidate_facts.get("turn_id") or state.commit_receipt.get("turn_id") or "")
    committed_turn_state = CommittedTurnState(
        turn_id=turn_id,
        commit_stage=commit_stage_id,
        rendered_text=rendered.rendered_text,
        pending_repair_state=dict(assembly.pending_repair_state),
        resolved_obligations=list(assembly.resolved_obligations),
        remaining_obligations=list(assembly.remaining_obligations),
        confirmed_user_facts=list(assembly.confirmed_user_facts),
    )
    return (
        replace(
            state,
            final_answer=rendered.rendered_text,
            pending_repair=assembly.pending_repair_state,
            commit_receipt=commit_receipt,
        ),
        committed_turn_state,
    )
