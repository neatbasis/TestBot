from __future__ import annotations

import re

from behave import given, then, when

from testbot.eval_fixtures import cases_by_id
from testbot.pipeline_state import CandidateHit, PipelineState
from testbot.stage_transitions import validate_answer_post, validate_answer_pre


CITATION_PATTERN = re.compile(r"doc_id\s*[:=]\s*[^,\]\)\n]+.*?ts\s*[:=]\s*[^,\]\)\n]+", re.IGNORECASE)


def _response_contains_claims(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if normalized == "I don't know from memory.":
        return False
    return bool(re.search(r"[A-Za-z0-9].{8,}", normalized))


def _validate_answer_contract(text: str) -> bool:
    if not _response_contains_claims(text):
        return True
    return bool(CITATION_PATTERN.search(text or ""))


@given('an uncited factual candidate from eval case "{case_id}"')
def step_given_uncited_candidate_from_eval_case(context, case_id: str) -> None:
    case = cases_by_id()[case_id]
    top_candidate = max(case.candidates, key=lambda candidate: candidate["sim_score"])
    context.candidate = top_candidate["text"]


@when("the answer contract validator checks the candidate")
def step_when_validate(context) -> None:
    context.contract_passed = _validate_answer_contract(context.candidate)
    context.pipeline_state = PipelineState(
        user_input="test question",
        rewritten_query="test question",
        retrieval_candidates=[CandidateHit(doc_id="doc-1", score=0.8, ts="2024-01-01T00:00:00Z", card_type="memory")],
        reranked_hits=[CandidateHit(doc_id="doc-1", score=0.8, ts="2024-01-01T00:00:00Z", card_type="memory")],
        confidence_decision={"context_confident": True},
        draft_answer=context.candidate,
        final_answer="I don't know from memory.",
        invariant_decisions={"answer_contract_valid": context.contract_passed},
    )
    context.answer_pre_check = validate_answer_pre(context.pipeline_state)
    context.answer_post_check = validate_answer_post(context.pipeline_state)


@then("the candidate is rejected")
def step_then_rejected(context) -> None:
    assert context.contract_passed is False
    assert context.answer_pre_check.passed, f"answer.pre failed: {context.answer_pre_check.failures}"
    assert context.answer_post_check.passed, f"answer.post failed: {context.answer_post_check.failures}"
