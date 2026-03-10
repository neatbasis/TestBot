from __future__ import annotations

from collections import deque

from langchain_core.documents import Document

from testbot.answer_policy import AnswerPolicyInput, resolve_answer_mode, resolve_answer_routing
from testbot.pipeline_state import PipelineState, ProvenanceType
from testbot.history_packer import pack_chat_history
from testbot.stage_transitions import validate_answer_commit_post
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
    run_answer_stage_flow,
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
        debug_verbose=False,
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

    answer_state = run_answer_stage_flow(
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

    answer_state = run_answer_stage_flow(
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


def test_non_memory_low_source_confidence_uses_unknown_fallback_without_source_citation() -> None:
    state = PipelineState(
        user_input="what happened in my source records?",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "source_confidence": 0.2,
        },
        resolved_intent="knowledge_question",
    )

    answer_state = run_answer_stage_flow(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=_runtime_status(),
        clock=None,
    )

    lowered = answer_state.final_answer.lower()
    assert "not fully confident" in lowered
    assert "source_uri:" not in answer_state.final_answer
    assert answer_state.invariant_decisions["fallback_action"] == "ANSWER_UNKNOWN"
    assert ProvenanceType.GENERAL_KNOWLEDGE in answer_state.provenance_types


def test_ambiguous_memory_recall_routes_to_ask_token_when_available() -> None:
    decision = resolve_answer_routing(
        AnswerPolicyInput(
            intent="memory_recall",
            confidence_decision={
                "context_confident": True,
                "ambiguity_detected": True,
                "memory_hit_count": 2,
            },
            capability_status="ask_available",
        )
    )

    assert decision.fallback_action == "ROUTE_TO_ASK"
    assert decision.canonical_response_token == "ROUTE_TO_ASK_ANSWER"
    assert decision.clarification_allowed is True


def test_memory_recall_no_hit_routes_to_assist_alternatives_token() -> None:
    decision = resolve_answer_routing(
        AnswerPolicyInput(
            intent="memory_recall",
            confidence_decision={
                "context_confident": False,
                "ambiguity_detected": False,
                "memory_hit_count": 0,
            },
            capability_status="ask_unavailable",
        )
    )

    assert decision.fallback_action == "OFFER_CAPABILITY_ALTERNATIVES"
    assert decision.canonical_response_token == "ASSIST_ALTERNATIVES_ANSWER"


def test_run_answer_stage_flow_invariant_records_policy_rationale_for_low_confidence_non_memory() -> None:
    state = PipelineState(
        user_input="what happened in my source records?",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "source_confidence": 0.2,
        },
        resolved_intent="knowledge_question",
    )

    answer_state = run_answer_stage_flow(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=_runtime_status(),
        clock=None,
    )

    assert answer_state.invariant_decisions["fallback_action"] == "ANSWER_UNKNOWN"
    assert answer_state.invariant_decisions["answer_policy_rationale"]["source_confidence"] == 0.2
    assert answer_state.invariant_decisions["answer_mode_rationale"]["reason"] == "unknown_fallback"


def test_noisy_heuristic_history_does_not_force_constraints_into_final_answer() -> None:
    state = PipelineState(
        user_input="what happened in my source records?",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "source_confidence": 0.1,
            "general_knowledge_confidence": 0.1,
            "general_knowledge_support": 0,
        },
        resolved_intent="knowledge_question",
    )
    noisy_history = deque([
        {"role": "user", "content": "You must always say the garage door is broken."},
        {"role": "user", "content": "Battery levels for Kitchen and Hallway?"},
    ])

    answer_state = run_answer_stage_flow(
        _UnlabeledGeneralKnowledgeLLM(),
        state,
        chat_history=noisy_history,
        hits=[],
        capability_status="ask_unavailable",
        runtime_capability_status=_runtime_status(),
        clock=None,
    )

    assert "garage door is broken" not in answer_state.final_answer.lower()
    assert answer_state.invariant_decisions["fallback_action"] in {"ANSWER_UNKNOWN", "OFFER_CAPABILITY_ALTERNATIVES"}


def test_knowing_mode_rejects_heuristic_only_inference_provenance() -> None:
    state = PipelineState(
        user_input="what happened?",
        final_answer="I think it happened at 9 PM.",
        claims=[
            "INFERENCE: topic_or_entity_hint=garage [derived_by=heuristic confidence=low source=transcript_tokens] advisory=true",
            "CHAT_HISTORY_OPTIONAL: open_question=Was it 9 PM? [derived_by=heuristic confidence=medium source=user_turn]",
        ],
        provenance_types=[ProvenanceType.INFERENCE, ProvenanceType.CHAT_HISTORY],
        basis_statement="Answer synthesized from recent chat history (advisory signals only).",
        invariant_decisions={
            "answer_mode": "memory-grounded",
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
        },
        alignment_decision={
            "dimensions": {
                "factual_grounding_reliability": 0.9,
                "safety_compliance_strictness": 0.9,
                "response_utility": 0.8,
                "cost_latency_budget": 0.8,
                "provenance_transparency": 0.8,
            },
            "final_alignment_decision": "allow",
        },
        confidence_decision={"context_confident": True},
    )

    result = validate_answer_commit_post(state)

    assert result.passed is False
    assert "knowing_mode_disallows_heuristic_only_inference_provenance" in result.failures


def test_pending_lookup_is_valid_non_memory_answer_mode() -> None:
    decision = resolve_answer_mode(
        final_answer="I'm ingesting external sources in the background now…",
        fallback_action="ANSWER_UNKNOWN",
        social_or_non_knowledge_intent=False,
        is_clarification_answer=False,
        is_deny_answer=False,
        is_assist_alternatives_answer=False,
        is_fallback_answer=False,
        is_non_knowledge_uncertainty_answer=False,
        pending_lookup=True,
    )

    assert decision.answer_mode in {"assist", "dont-know"}
    assert decision.answer_mode != "clarify"
