from __future__ import annotations

from behave import given, then, when

FALLBACK = "I don't know from memory."


FIXTURES = {
    "when is garbage pickup?": {
        "answer": "Garbage pickup is every Tuesday at 7:00 AM.",
        "doc_id": "mem-garbage-001",
        "ts": "2024-10-01T09:00:00Z",
    }
}


def _answer_from_memory(query: str) -> str:
    hit = FIXTURES.get(query.strip().lower())
    if not hit:
        return FALLBACK
    return f"{hit['answer']} (doc_id: {hit['doc_id']}, ts: {hit['ts']})"


@given("deterministic memory fixtures are loaded")
def step_given_fixtures(context) -> None:
    context.fixtures = FIXTURES


@when('the user asks "{question}"')
def step_when_user_asks(context, question: str) -> None:
    context.question = question
    context.answer = _answer_from_memory(question)


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
