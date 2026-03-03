from __future__ import annotations

import re

from behave import given, then, when

from testbot.eval_fixtures import cases_by_id


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


@then("the candidate is rejected")
def step_then_rejected(context) -> None:
    assert context.contract_passed is False
