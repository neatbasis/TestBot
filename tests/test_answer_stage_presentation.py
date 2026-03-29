from __future__ import annotations

from langchain_core.documents import Document

from testbot.application.services import answer_stage_presentation as canonical


def test_render_context_emits_expected_structured_fields() -> None:
    rendered = canonical.render_context(
        [
            Document(
                page_content="  The user asked about training schedule.  ",
                metadata={"doc_id": "mem-42", "ts": "2026-03-06T08:15:00Z", "type": "memory_card"},
            )
        ]
    )

    assert "[doc_1]" in rendered
    assert "doc_id: mem-42" in rendered
    assert "ts: 2026-03-06T08:15:00Z" in rendered
    assert "type: memory_card" in rendered
    assert "content: The user asked about training schedule." in rendered


def test_render_context_respects_limit_chars_truncation_boundary() -> None:
    docs = [
        Document(page_content="alpha", metadata={"doc_id": "d1", "ts": "t1", "type": "memory"}),
        Document(page_content="beta", metadata={"doc_id": "d2", "ts": "t2", "type": "memory"}),
    ]

    full = canonical.render_context(docs, limit_chars=5_000)
    limited = canonical.render_context(docs, limit_chars=80)

    assert "doc_id: d1" in full and "doc_id: d2" in full
    assert "doc_id: d1" in limited
    assert "doc_id: d2" not in limited


def test_answer_prompt_retains_required_guardrail_language() -> None:
    system_template = canonical.ANSWER_PROMPT.messages[0].prompt.template

    assert "Use ONLY the provided memory context and recent chat." in system_template
    assert "Heuristic packed-history hints are advisory context only, never hard evidence." in system_template
    assert "include at least one cited memory with both doc_id and ts" in system_template
