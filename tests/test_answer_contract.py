from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

from testbot.pipeline_state import PipelineState, ProvenanceType
from testbot.history_packer import pack_chat_history
from testbot.sat_chatbot_memory_v2 import (
    ASSIST_ALTERNATIVES_ANSWER,
    FALLBACK_ANSWER,
    RuntimeCapabilityStatus,
    build_provenance_metadata,
    evaluate_alignment_decision,
    raw_claim_like_text_detected,
    response_contains_claims,
    stage_answer,
)


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

    lowered = answer_state.final_answer.lower()
    assert "don't have enough reliable" in lowered
    assert "i can either" in lowered and " or " in lowered
    assert "Which person, event, or time window should I focus on?" not in answer_state.final_answer
    assert answer_state.invariant_decisions["answer_mode"] != "clarify"


def test_memory_recall_confident_contract_failure_uses_deterministic_recovery_hit() -> None:
    state = PipelineState(
        user_input="what did i decide about training schedule?",
        confidence_decision={
            "context_confident": True,
            "ambiguity_detected": False,
        },
        resolved_intent="memory_recall",
    )
    hits = [
        Document(
            page_content="You decided to move strength training to Tuesday mornings after the team standup.",
            metadata={"doc_id": "mem-42", "ts": "2026-03-06T08:15:00Z"},
        )
    ]

    answer_state = stage_answer(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=deque(),
        hits=hits,
        capability_status="ask_unavailable",
        runtime_capability_status=_runtime_status(),
        clock=None,
    )

    assert answer_state.final_answer != ASSIST_ALTERNATIVES_ANSWER
    assert "From memory, I found:" in answer_state.final_answer
    assert "doc_id: mem-42" in answer_state.final_answer
    assert "ts: 2026-03-06T08:15:00Z" in answer_state.final_answer
    assert answer_state.invariant_decisions["answer_mode"] == "memory-grounded"



def test_response_contains_claims_matches_extracted_claim_artifacts_for_fallback_text() -> None:
    packed_history = pack_chat_history([])
    _provenance, claims, _basis, _memory_refs, _source_refs, _source_attr = build_provenance_metadata(
        final_answer=FALLBACK_ANSWER,
        hits=[],
        chat_history=deque(),
        packed_history=packed_history,
    )

    assert claims == []
    assert response_contains_claims(FALLBACK_ANSWER) is False
    assert bool(claims) is False


def test_response_contains_claims_matches_extracted_claim_artifacts_for_factual_text() -> None:
    answer = "Marie Curie won two Nobel Prizes. doc_id: c-1 ts: 1903-12-10T00:00:00Z"
    packed_history = pack_chat_history([])
    _provenance, claims, _basis, _memory_refs, _source_refs, _source_attr = build_provenance_metadata(
        final_answer=answer,
        hits=[],
        chat_history=deque(),
        packed_history=packed_history,
    )

    assert claims
    assert response_contains_claims(answer) is True
    assert bool(claims) is True


def test_response_contains_claims_matches_extracted_claim_artifacts_for_greeting_text() -> None:
    answer = "Hey there! Nice to see you."
    packed_history = pack_chat_history([])
    _provenance, claims, _basis, _memory_refs, _source_refs, _source_attr = build_provenance_metadata(
        final_answer=answer,
        hits=[],
        chat_history=deque(),
        packed_history=packed_history,
    )

    assert claims
    assert response_contains_claims(answer) is True
    assert bool(claims) is True


def test_raw_claim_like_text_detected_is_exposed_for_alignment_inputs() -> None:
    decision = evaluate_alignment_decision(
        user_input="hello",
        draft_answer="hello there",
        final_answer="hello there",
        confidence_decision={"context_confident": True},
        claims=["INFERENCE: hello there"],
        provenance_types=[ProvenanceType.INFERENCE],
        basis_statement="Answer synthesized from recent chat history.",
    )

    assert raw_claim_like_text_detected("hello there") is True
    assert decision["dimension_inputs"]["raw"]["raw_claim_like_text_detected"] is True
