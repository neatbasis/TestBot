from __future__ import annotations

from collections import deque

import pytest
from langchain_core.documents import Document

from testbot.application.services import answer_stage_presentation as canonical_presentation
from testbot.pipeline_state import PipelineState
from testbot import sat_chatbot_memory_v2 as runtime


def test_run_answer_stage_flow_deprecated_alias_warns_and_delegates(monkeypatch) -> None:
    state = PipelineState(user_input="hello")
    expected = PipelineState(user_input="hello", final_answer="ok")
    observed: dict[str, object] = {}

    def _fake_canonical_flow(*args, **kwargs):
        observed["called"] = True
        return expected

    monkeypatch.setattr(runtime, "run_canonical_answer_stage_flow", _fake_canonical_flow)

    with pytest.deprecated_call(match="run_answer_stage_flow"):
        actual = runtime.run_answer_stage_flow(
            llm=object(),
            state=state,
            chat_history=deque(),
            hits=[],
            capability_status="ask_unavailable",
        )

    assert actual is expected
    assert observed["called"] is True


def test_run_canonical_answer_stage_flow_compat_delegates_to_runtime_service(monkeypatch) -> None:
    state = PipelineState(user_input="hello")
    expected = PipelineState(user_input="hello", final_answer="ok")
    observed: dict[str, object] = {}

    def _fake_run_flow(*args, **kwargs):
        observed["called"] = True
        return expected

    monkeypatch.setattr(runtime.answer_stage_runtime_service, "run_canonical_answer_stage_flow", _fake_run_flow)

    actual = runtime.run_canonical_answer_stage_flow(
        llm=object(),
        state=state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
    )

    assert actual is expected
    assert observed["called"] is True


def test_answer_prompt_compat_reexport_matches_canonical_owner() -> None:
    assert runtime.ANSWER_PROMPT is canonical_presentation.ANSWER_PROMPT


def test_render_context_compat_wrapper_matches_canonical_owner() -> None:
    docs = [Document(page_content="x", metadata={"doc_id": "d1", "ts": "t1", "type": "memory"})]

    assert runtime.render_context(docs, limit_chars=5000) == canonical_presentation.render_context(docs, limit_chars=5000)
