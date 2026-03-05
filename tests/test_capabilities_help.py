from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import CAPABILITIES_HELP_ANSWER, stage_answer


class _FailIfInvokedLLM:
    def invoke(self, _msgs):  # pragma: no cover - should never be reached
        raise AssertionError("LLM should not run for capabilities-help intent")


def test_stage_answer_capabilities_help_is_stable_across_memory_conditions() -> None:
    state = PipelineState(
        user_input="what can you do",
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )

    without_hits = stage_answer(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        clock=None,
    )
    with_hits = stage_answer(
        _FailIfInvokedLLM(),
        state,
        chat_history=deque(),
        hits=[Document(page_content="memory", metadata={"doc_id": "d-1", "ts": "2025-01-01T00:00:00Z"})],
        capability_status="ask_available",
        clock=None,
    )

    assert without_hits.final_answer == CAPABILITIES_HELP_ANSWER
    assert with_hits.final_answer == CAPABILITIES_HELP_ANSWER
    assert without_hits.draft_answer == ""
    assert with_hits.draft_answer == ""
