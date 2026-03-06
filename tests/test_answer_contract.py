from __future__ import annotations

from collections import deque

from testbot.pipeline_state import PipelineState
from testbot.sat_chatbot_memory_v2 import RuntimeCapabilityStatus, stage_answer


class _UnlabeledGeneralKnowledgeLLM:
    class _Response:
        content = "Ontology is the study of being and existence."

    def invoke(self, _msgs):
        return self._Response()


def _runtime_status() -> RuntimeCapabilityStatus:
    return RuntimeCapabilityStatus(
        ollama_available=True,
        ha_available=False,
        effective_mode="cli",
        requested_mode="cli",
        daemon_mode=False,
        fallback_reason=None,
        memory_backend="in_memory",
        debug_enabled=False,
        text_clarification_available=True,
        satellite_ask_available=False,
    )


def test_non_memory_general_knowledge_contract_failure_degrades_to_knowledge_safe_response() -> None:
    state = PipelineState(
        user_input="what is ontology?",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": True,
            "general_knowledge_confidence": 0.1,
            "general_knowledge_support": 0,
        },
        resolved_intent="knowledge_question",
    )

    answer_state = stage_answer(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=_runtime_status(),
        clock=None,
    )

    assert answer_state.final_answer == "I don't know from memory."
    assert "Which person, event, or time window should I focus on?" not in answer_state.final_answer
    assert answer_state.invariant_decisions["answer_mode"] != "clarify"
