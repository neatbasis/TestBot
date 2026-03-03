from __future__ import annotations

from behave import given, then, when

from testbot.eval_fixtures import best_candidate_doc_id, cases_by_id

FALLBACK = "I don't know from memory."


def _answer_from_case(case_id: str, loaded_cases) -> str:
    case = loaded_cases[case_id]
    chosen_doc_id = best_candidate_doc_id(case)
    if not chosen_doc_id:
        return FALLBACK

    chosen = next(candidate for candidate in case.candidates if candidate["doc_id"] == chosen_doc_id)
    return f"{chosen['text']} (doc_id: {chosen['doc_id']}, ts: {chosen['ts']})"


@given("a deterministic in-memory recall harness")
def step_given_deterministic_harness(context) -> None:
    """BDD default path intentionally avoids live HA/Ollama integrations."""
    context.live_dependencies = {"home_assistant": False, "ollama": False}


@given('eval cases are loaded from "{cases_path}"')
def step_given_cases_loaded(context, cases_path: str) -> None:
    del cases_path  # path is fixed via shared loader until alternate case files are needed.
    context.eval_cases = cases_by_id()


@when('the user asks about eval case "{case_id}"')
def step_when_user_asks_eval_case(context, case_id: str) -> None:
    context.case_id = case_id
    context.answer = _answer_from_case(case_id, context.eval_cases)


@then("the assistant returns a memory-grounded answer")
def step_then_grounded(context) -> None:
    assert context.answer != FALLBACK


@then('the answer includes citation fields "doc_id" and "ts"')
def step_then_has_citation(context) -> None:
    assert "doc_id:" in context.answer
    assert "ts:" in context.answer


@then('the assistant responds exactly "I don\'t know from memory."')
def step_then_exact_fallback(context) -> None:
    assert context.answer == FALLBACK
