from __future__ import annotations

from dataclasses import dataclass

from testbot.answer_assembly import AnswerCandidate
from testbot.answer_validation import ValidatedAnswer


@dataclass(frozen=True)
class RenderedAnswer:
    rendered_text: str
    repair_offer_rendered: bool = False
    repair_followup_route: str = ""


def render_answer(*, assembly: AnswerCandidate, validation: ValidatedAnswer, preferred_text: str = "") -> RenderedAnswer:
    if not validation.passed:
        raise ValueError("cannot render answer before assembly validation passes")

    if preferred_text.strip():
        text = preferred_text
    elif validation.final_answer.strip():
        text = validation.final_answer
    elif assembly.pending_repair_state.get("repair_required_by_policy"):
        text = (
            "I don't have enough reliable memory to answer directly. "
            "I can help continue repair reconstruction from the details we already confirmed."
        )
        return RenderedAnswer(
            rendered_text=text,
            repair_offer_rendered=True,
            repair_followup_route="repair_offer_followup",
        )
    else:
        text = "I can answer from the currently validated decision and evidence bundle."
    return RenderedAnswer(rendered_text=text)
