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
    has_required_memory_citation,
    raw_claim_like_text_detected,
    render_context,
    response_contains_claims,
    stage_answer,
    validate_answer_contract,
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


def test_render_context_includes_structured_memory_fields_for_citations() -> None:
    docs = [
        Document(
            page_content="  Team agreed to move weekly planning to Thursdays at 09:00.  ",
            metadata={
                "doc_id": "mem-100",
                "ts": "2026-03-05T09:00:00Z",
                "type": "decision",
            },
        ),
        Document(
            page_content="Second note without explicit type still renders deterministically.",
            metadata={
                "doc_id": "mem-101",
                "ts": "2026-03-06T11:30:00Z",
            },
        ),
    ]

    rendered = render_context(docs)

    assert rendered == (
        "[doc_1]\n"
        "doc_id: mem-100\n"
        "ts: 2026-03-05T09:00:00Z\n"
        "type: decision\n"
        "content: Team agreed to move weekly planning to Thursdays at 09:00.\n"
        "---\n"
        "[doc_2]\n"
        "doc_id: mem-101\n"
        "ts: 2026-03-06T11:30:00Z\n"
        "type: \n"
        "content: Second note without explicit type still renders deterministically.\n"
        "---"
    )


def test_rendered_context_supports_synthetic_citation_valid_draft_path() -> None:
    docs = [
        Document(
            page_content="The training schedule was moved to Tuesday mornings.",
            metadata={
                "doc_id": "mem-42",
                "ts": "2026-03-06T08:15:00Z",
                "type": "plan",
            },
        )
    ]

    context = render_context(docs)
    synthetic_draft = (
        "From memory: training is Tuesday morning (doc_id: mem-42, ts: 2026-03-06T08:15:00Z)."
    )

    assert "doc_id: mem-42" in context
    assert "ts: 2026-03-06T08:15:00Z" in context
    assert has_required_memory_citation(synthetic_draft) is True
    assert validate_answer_contract(synthetic_draft) is True
