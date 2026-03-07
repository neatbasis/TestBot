from __future__ import annotations

from dataclasses import replace

from testbot.answer_assembly import AnswerAssemblyResult
from testbot.answer_rendering import RenderedAnswer
from testbot.answer_validation import AnswerValidationResult
from testbot.pipeline_state import CommitReceiptArtifact, PipelineState


def commit_answer_stage(
    state: PipelineState,
    *,
    assembly: AnswerAssemblyResult,
    validation: AnswerValidationResult,
    rendered: RenderedAnswer,
    commit_stage_id: str = "answer.commit",
) -> PipelineState:
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
    return replace(
        state,
        final_answer=rendered.rendered_text,
        pending_repair=assembly.pending_repair_state,
        commit_receipt=commit_receipt,
    )
