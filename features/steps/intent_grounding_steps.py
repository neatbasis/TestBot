from __future__ import annotations

from collections import deque
from dataclasses import replace

from behave import given, then, when
from langchain_core.documents import Document

from testbot.history_packer import PackedHistory
from testbot.intent_router import IntentType, classify_intent
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.sat_chatbot_memory_v2 import (
    ROUTE_TO_ASK_ANSWER,
    build_provenance_metadata,
    resolve_turn_intent,
    validate_general_knowledge_contract,
)
from testbot.stage_transitions import validate_answer_post, validate_answer_pre

GENERAL_MARKER = "General definition (not from your memory):"


@given("an intent response harness")
def step_given_intent_response_harness(context) -> None:
    context.candidates = []


def _build_base_state(*, user_input: str, final_answer: str, draft_answer: str, confidence_decision: dict[str, object]) -> PipelineState:
    state = PipelineState(
        user_input=user_input,
        rewritten_query=user_input,
        retrieval_candidates=[CandidateHit(doc_id="", score=0.0, ts="", card_type="memory")],
        reranked_hits=[],
        confidence_decision=confidence_decision,
        draft_answer=draft_answer,
        final_answer=final_answer,
        claims=[f"INFERENCE: {final_answer}"],
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": "memory-grounded",
            "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
        },
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 1.0,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "allow",
        },
    )
    return state


def _run_contract_checks(context) -> None:
    context.answer_pre_check = validate_answer_pre(context.pipeline_state)
    context.answer_post_check = validate_answer_post(context.pipeline_state)
    assert context.answer_pre_check.passed, f"answer.pre failed: {context.answer_pre_check.failures}"
    assert context.answer_post_check.passed, f"answer.post failed: {context.answer_post_check.failures}"


@when("a knowledge question misses memory context")
def step_when_knowledge_memory_miss(context) -> None:
    answer = (
        "General definition (not from your memory): Ontology is a formal representation of concepts and their "
        "relationships. Can you clarify which domain you want this applied to?"
    )
    context.pipeline_state = _build_base_state(
        user_input="What is ontology?",
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={
            "context_confident": True,
            "general_knowledge_confidence": 0.95,
            "general_knowledge_support": 3,
        },
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.GENERAL_KNOWLEDGE, ProvenanceType.INFERENCE],
        basis_statement="General-knowledge basis: no supporting memory references were retrieved.",
    )
    context.gk_contract_passed = validate_general_knowledge_contract(
        context.pipeline_state.final_answer,
        provenance_types=context.pipeline_state.provenance_types,
        confidence_decision=context.pipeline_state.confidence_decision,
    )
    context.pipeline_state.invariant_decisions["general_knowledge_contract_valid"] = context.gk_contract_passed
    _run_contract_checks(context)


@when('the user asks "what did I ask?"')
def step_when_meta_what_did_i_ask(context) -> None:
    context.intent = classify_intent("what did I ask?")
    answer = "You asked about ontology earlier in this chat."
    context.pipeline_state = _build_base_state(
        user_input="what did I ask?",
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={"context_confident": True},
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.CHAT_HISTORY, ProvenanceType.INFERENCE],
        basis_statement="Answer synthesized from recent chat history.",
    )
    _run_contract_checks(context)


@when("the user asks a relevance question")
def step_when_relevance_question(context) -> None:
    prompt = "what's relevant to our conversation?"
    context.intent = classify_intent(prompt)
    answer = "Relevant summary: we focused on ontology definitions and next-step clarifications for this chat."
    context.pipeline_state = _build_base_state(
        user_input=prompt,
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={"context_confident": True},
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.CHAT_HISTORY, ProvenanceType.INFERENCE],
        basis_statement="Relevance summary basis: synthesized from recent chat history signals.",
    )
    _run_contract_checks(context)


@when("the user asks a source-backed knowing question")
def step_when_source_backed_knowing_question(context) -> None:
    answer = "Your next power utility event is Friday at 7pm (source_uri: calendar://work/event-42)."
    context.pipeline_state = _build_base_state(
        user_input="When is my next utility event?",
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={"context_confident": True, "source_confidence": 0.93},
    )
    hit = CandidateHit(
        doc_id="src-42",
        score=0.92,
        ts="2026-03-10T09:00:00Z",
        card_type="source_evidence",
    )
    context.pipeline_state = replace(context.pipeline_state, reranked_hits=[hit])
    provenance, _claims, basis, memory_refs, source_refs, source_attr = build_provenance_metadata(
        final_answer=context.pipeline_state.final_answer,
        hits=[
            Document(
                id="src-42",
                page_content="utility event",
                metadata={
                    "type": "source_evidence",
                    "source_type": "calendar",
                    "source_uri": "calendar://work/event-42",
                    "retrieved_at": "2026-03-10T09:00:00Z",
                    "trust_tier": "high",
                },
            )
        ],
        chat_history=deque(),
        packed_history=PackedHistory([], [], [], [], []),
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=provenance,
        basis_statement=basis,
        used_memory_refs=memory_refs,
        used_source_evidence_refs=source_refs,
        source_evidence_attribution=source_attr,
    )
    _run_contract_checks(context)


@when("source confidence is insufficient for a knowing answer")
def step_when_source_confidence_insufficient(context) -> None:
    context.pipeline_state = _build_base_state(
        user_input="What happened in my calendar?",
        final_answer="I don't have enough reliable context to answer directly. I can either help you narrow the source or suggest where to verify the detail.",
        draft_answer="",
        confidence_decision={"context_confident": True, "source_confidence": 0.35},
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.UNKNOWN],
        basis_statement="Trivial fallback/deny/clarification response with no substantive claim.",
        alignment_decision={
            "objective_version": "2026-03-01.v1",
            "dimensions": {
                "factual_grounding_reliability": 1.0,
                "safety_compliance_strictness": 1.0,
                "response_utility": 1.0,
                "cost_latency_budget": 1.0,
                "provenance_transparency": 1.0,
            },
            "final_alignment_decision": "allow",
        },
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": "assist",
            "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
        },
    )
    _run_contract_checks(context)


@then("the assistant returns a labeled general answer with clarification")
def step_then_labeled_general_answer(context) -> None:
    assert context.pipeline_state.final_answer.startswith(GENERAL_MARKER)
    assert "Can you clarify" in context.pipeline_state.final_answer


@then("the response records general-knowledge provenance and basis")
def step_then_general_knowledge_provenance(context) -> None:
    assert context.gk_contract_passed is True
    assert ProvenanceType.GENERAL_KNOWLEDGE in context.pipeline_state.provenance_types
    assert "General-knowledge basis" in context.pipeline_state.basis_statement


@then("the assistant replies from chat history")
def step_then_chat_history_reply(context) -> None:
    assert context.intent is IntentType.MEMORY_RECALL
    assert "asked about ontology" in context.pipeline_state.final_answer


@then("the response records chat-history provenance and basis")
def step_then_chat_history_provenance(context) -> None:
    assert ProvenanceType.CHAT_HISTORY in context.pipeline_state.provenance_types
    assert "chat history" in context.pipeline_state.basis_statement.lower()


@then("the assistant returns a summarized relevance answer")
def step_then_relevance_summary(context) -> None:
    assert context.intent is IntentType.META_CONVERSATION
    assert context.pipeline_state.final_answer.startswith("Relevant summary:")


@then("the response includes a relevance basis assertion")
def step_then_relevance_basis(context) -> None:
    assert "Relevance summary basis:" in context.pipeline_state.basis_statement
    assert "chat history" in context.pipeline_state.basis_statement.lower()


@then("the assistant returns a source-backed answer with citation")
def step_then_source_backed_answer_with_citation(context) -> None:
    assert "source_uri:" in context.pipeline_state.final_answer
    assert context.pipeline_state.used_source_evidence_refs == ["src-42"]


@then('the source provenance includes "{source_uri}" and "{source_type}"')
def step_then_source_provenance_includes_fields(context, source_uri: str, source_type: str) -> None:
    assert context.pipeline_state.source_evidence_attribution
    attribution = context.pipeline_state.source_evidence_attribution[0]
    assert attribution["source_uri"] == source_uri
    assert attribution["source_type"] == source_type


@then("the assistant returns a progressive unknowing response")
def step_then_explicit_unknowing_fallback(context) -> None:
    lowered = context.pipeline_state.final_answer.lower()
    assert "either" in lowered and "or" in lowered
    assert context.pipeline_state.provenance_types == [ProvenanceType.UNKNOWN]


@then("the response should include explicit uncertainty language")
def step_then_response_includes_explicit_uncertainty_language(context) -> None:
    lowered = context.pipeline_state.final_answer.lower()
    assert "don't have enough reliable" in lowered or "don't know" in lowered


@then("the response should include a safe action path")
def step_then_response_includes_safe_action_path(context) -> None:
    lowered = context.pipeline_state.final_answer.lower()
    assert "i can either" in lowered
    assert " or " in lowered


@then('the response should include "{expected_substring}"')
def step_then_response_includes_substring(context, expected_substring: str) -> None:
    assert expected_substring in context.pipeline_state.final_answer


@then('the provenance and basis should include "{provenance_name}" and "{basis_text}"')
def step_then_provenance_and_basis_include(context, provenance_name: str, basis_text: str) -> None:
    assert any(provenance.name == provenance_name for provenance in context.pipeline_state.provenance_types)
    assert basis_text.lower() in context.pipeline_state.basis_statement.lower()


@when('the user asks to ask something via satellite and follows up with "yes"')
def step_when_affirmation_followup_continuity(context) -> None:
    first_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        classified_intent=IntentType.KNOWLEDGE_QUESTION.value,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )
    context.followup_classified, context.followup_resolved = resolve_turn_intent(
        utterance="yes",
        prior_pipeline_state=first_state,
    )


@then("the resolved follow-up intent should preserve capabilities help continuity")
def step_then_followup_preserves_capabilities_intent(context) -> None:
    assert context.followup_classified is IntentType.KNOWLEDGE_QUESTION
    assert context.followup_resolved is IntentType.CAPABILITIES_HELP



@when("a non-memory knowledge question has no ambiguity")
def step_when_non_memory_direct_answer(context) -> None:
    context.intent = classify_intent("What is ontology?")
    answer = "General definition (not from your memory): Ontology organizes concepts and relations."
    context.pipeline_state = _build_base_state(
        user_input="What is ontology?",
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "retrieval_branch": "direct_answer",
            "general_knowledge_confidence": 0.96,
            "general_knowledge_support": 3,
        },
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.GENERAL_KNOWLEDGE, ProvenanceType.INFERENCE],
        basis_statement="General-knowledge basis: no supporting memory references were retrieved.",
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": "assist",
            "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
        },
    )
    _run_contract_checks(context)


@then("the response should remain in direct knowledge-answer flow")
def step_then_non_memory_direct_answer_flow(context) -> None:
    assert context.intent is IntentType.KNOWLEDGE_QUESTION
    assert context.pipeline_state.confidence_decision.get("retrieval_branch") == "direct_answer"
    assert not context.pipeline_state.final_answer.startswith("I found related memory fragments (")


@then("the response should not use clarifier mode")
def step_then_response_should_not_use_clarifier_mode(context) -> None:
    assert context.pipeline_state.invariant_decisions.get("answer_mode") != "clarify"
    assert "Can you clarify" not in context.pipeline_state.final_answer

@when("the user asks an ambiguous control-help-memory phrase")
def step_when_ambiguous_control_help_memory_phrase(context) -> None:
    context.ambiguous_intent = classify_intent("stop, can you help me remember what did I ask?")


@then("the utterance should route to control intent deterministically")
def step_then_ambiguous_control_help_memory_phrase(context) -> None:
    assert context.ambiguous_intent is IntentType.CONTROL


@when("the user asks an ambiguous satellite-versus-meta phrase")
def step_when_ambiguous_satellite_meta_phrase(context) -> None:
    context.ambiguous_intent = classify_intent("use satellite about this chat")


@then("the utterance should route to capabilities help intent deterministically")
def step_then_ambiguous_satellite_meta_phrase(context) -> None:
    assert context.ambiguous_intent is IntentType.CAPABILITIES_HELP


@when("the user asks an unmatched ambiguous phrase")
def step_when_unmatched_ambiguous_phrase(context) -> None:
    context.ambiguous_intent = classify_intent("this seems mixed and maybe relevant")


@then("the utterance should route to knowledge-question fallback deterministically")
def step_then_unmatched_ambiguous_phrase(context) -> None:
    assert context.ambiguous_intent is IntentType.KNOWLEDGE_QUESTION
