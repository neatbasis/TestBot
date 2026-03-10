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
    else:
        text = ""

    offer_bearing = (
        bool(assembly.pending_repair_state.get("repair_offered_to_user"))
        and not assembly.pending_repair_state.get("repair_required_by_policy")
    )

    if assembly.pending_repair_state.get("repair_required_by_policy"):
        if assembly.decision_class == "pending_lookup_background_ingestion":
            if text.strip():
                return RenderedAnswer(rendered_text=text)
            return RenderedAnswer(rendered_text="I'm ingesting external sources in the background now…")
        canned = (
            "I don't have enough reliable memory to answer directly. "
            "I can help continue repair reconstruction from the details we already confirmed."
        )
        return RenderedAnswer(
            rendered_text=canned,
            repair_offer_rendered=True,
            repair_followup_route="repair_offer_followup",
        )

    if offer_bearing and text.strip():
        return RenderedAnswer(
            rendered_text=text,
            repair_offer_rendered=True,
            repair_followup_route=str(assembly.pending_repair_state.get("offer_type") or "repair_offer_followup"),
        )

    if text.strip():
        return RenderedAnswer(rendered_text=text)

    return RenderedAnswer(rendered_text="I can answer from the currently validated decision and evidence bundle.")
