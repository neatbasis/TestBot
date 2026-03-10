from testbot.answer_assembly import AnswerCandidate
from testbot.answer_rendering import render_answer
from testbot.answer_validation import ValidatedAnswer


def test_render_answer_marks_offer_bearing_text_as_repair_offer_rendered() -> None:
    assembly = AnswerCandidate(
        decision_class="answer_general_knowledge_labeled",
        rendered_class="answer_general_knowledge_labeled",
        retrieval_branch="direct_answer",
        rationale="offer-bearing answer",
        evidence_counts={"structured_facts": 0},
        pending_repair_state={
            "repair_required_by_policy": False,
            "repair_offered_to_user": True,
            "offer_type": "capability_offer",
            "reason": "offer_bearing_answer",
        },
        pending_ingestion_request_id="",
        resolved_obligations=[],
        remaining_obligations=[],
        confirmed_user_facts=[],
    )
    validation = ValidatedAnswer(passed=True, failures=[], final_answer="I can look that up for you.")

    rendered = render_answer(assembly=assembly, validation=validation)

    assert rendered.rendered_text == "I can look that up for you."
    assert rendered.repair_offer_rendered is True
    assert rendered.repair_followup_route == "capability_offer"
