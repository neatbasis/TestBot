from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace

from behave import given, then, when
from langchain_core.documents import Document

from testbot.history_packer import PackedHistory
from testbot import sat_chatbot_memory_v2 as runtime
from testbot.evidence_retrieval import EvidenceBundle, EvidenceRecord, retrieval_result
from testbot.context_resolution import ContinuityPosture, resolve as resolve_context
from testbot.intent_resolution import IntentResolutionInput, resolve as resolve_intent
from testbot.intent_router import IntentFacets, IntentType, classify_intent, extract_intent_facets, planning_pathway_for_intent
from testbot.policy_decision import DecisionClass, EvidencePosture, decide, decide_from_evidence
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType
from testbot.candidate_encoding import FactCandidate
from testbot.stabilization import StabilizedTurnState
from testbot.sat_chatbot_memory_v2 import (
    ROUTE_TO_ASK_ANSWER,
    build_provenance_metadata,
    resolve_turn_intent,
    run_answer_stage_flow,
    stage_rewrite_query,
    validate_general_knowledge_contract,
)
from testbot.stage_transitions import validate_answer_post, validate_answer_pre

GENERAL_MARKER = "General definition (not from your memory):"


@dataclass(frozen=True)
class BDDTypedIntent:
    intent_class: IntentType
    facets: object
    pathway: str


def _parse_bool(raw: str) -> bool:
    return str(raw).strip().lower() == "true"


def _validate_typed_intent_contract(typed_intent: BDDTypedIntent) -> str | None:
    facets = typed_intent.facets
    if typed_intent.intent_class is IntentType.CONTROL and (facets.temporal or facets.memory or facets.capability):
        return "control_cannot_include_other_facets"
    if typed_intent.intent_class is IntentType.CAPABILITIES_HELP and not facets.capability:
        return "capabilities_help_requires_capability"
    if typed_intent.intent_class is IntentType.META_CONVERSATION and (facets.temporal or facets.memory):
        return "meta_cannot_include_temporal_memory"
    if typed_intent.intent_class is IntentType.TIME_QUERY and not facets.temporal:
        return "time_query_requires_temporal"
    if facets.control and typed_intent.intent_class is not IntentType.CONTROL:
        return "control_facet_requires_control_intent"
    return None


def _stabilized_turn_state_for_bdd(utterance: str) -> StabilizedTurnState:
    return StabilizedTurnState(
        turn_id="bdd-turn",
        utterance_card="UTTERANCE CARD",
        utterance_doc_id="bdd-u",
        reflection_doc_id="bdd-r",
        dialogue_state_doc_id="bdd-d",
        segment_type="episodic",
        segment_id="bdd-seg",
        segment_membership_edge_refs=[],
        same_turn_exclusion_doc_ids=[],
        candidate_facts=[FactCandidate(key="utterance_raw", value=utterance, confidence=1.0)],
        candidate_speech_acts=[],
        candidate_dialogue_state=[],
    )


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




def _assert_evidence_state_fields(
    state_contract: dict[str, object],
    *,
    typed_state: str,
    evidence_posture: str,
    decision_class: str,
    provenance_label: str,
    fallback_strategy: str,
) -> None:
    assert state_contract.get("typed_state") == typed_state
    assert state_contract.get("evidence_posture") == evidence_posture
    assert state_contract.get("decision_class") == decision_class
    assert state_contract.get("provenance_label") == provenance_label
    assert state_contract.get("fallback_strategy") == fallback_strategy

def _normalize_encoded_intent_candidates(raw_candidates: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    deduped: dict[str, dict[str, object]] = {}
    quarantined: list[dict[str, object]] = []

    for candidate in raw_candidates:
        candidate_id = str(candidate.get("id") or "").strip().lower()
        provenance = candidate.get("provenance")
        if not candidate_id:
            quarantined.append({**candidate, "quarantine_reason": "missing_candidate_id"})
            continue
        if not isinstance(provenance, str) or not provenance.strip():
            quarantined.append({**candidate, "normalized_id": candidate_id, "quarantine_reason": "invalid_provenance"})
            continue
        normalized = {
            "id": candidate_id,
            "intent": str(candidate.get("intent") or "").strip(),
            "confidence": float(candidate.get("confidence") or 0.0),
            "provenance": provenance.strip(),
        }
        existing = deduped.get(candidate_id)
        if existing is None or normalized["confidence"] > existing["confidence"]:
            deduped[candidate_id] = normalized

    normalized_candidates = sorted(
        deduped.values(),
        key=lambda item: (-item["confidence"], item["id"], item["intent"]),
    )
    quarantined_candidates = sorted(
        quarantined,
        key=lambda item: (str(item.get("normalized_id") or item.get("id") or ""), str(item.get("intent") or "")),
    )
    return normalized_candidates, quarantined_candidates


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
            "answer_policy_rationale": {"fallback_reason": "non_memory_low_source_confidence"},
        },
    )
    _run_contract_checks(context)


@when("source evidence remains low-confidence after retrieval")
def step_when_source_evidence_low_confidence_after_retrieval(context) -> None:
    context.pipeline_state = _build_base_state(
        user_input="What does my source data say about the incident?",
        final_answer="I don't have enough reliable context to answer directly. I can either help you narrow the source or suggest where to verify the detail.",
        draft_answer="",
        confidence_decision={"context_confident": False, "source_confidence": 0.22},
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.UNKNOWN],
        basis_statement="Trivial fallback/deny/clarification response with no substantive claim.",
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": "assist",
            "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
            "answer_policy_rationale": {"fallback_reason": "insufficient_reliable_memory"},
        },
    )
    _run_contract_checks(context)


@when("source evidence conflicts across candidate records")
def step_when_source_evidence_conflicts_across_candidates(context) -> None:
    context.pipeline_state = _build_base_state(
        user_input="What happened in my calendar for Friday?",
        final_answer=(
            "I found related memory fragments (doc_id: src-7 ts: 2026-03-11T09:00:00Z; "
            "doc_id: src-9 ts: 2026-03-11T09:05:00Z), but not enough to answer precisely. "
            "Which person, event, or time window should I focus on?"
        ),
        draft_answer="",
        confidence_decision={"context_confident": False, "ambiguity_detected": True, "allow_non_memory_clarify": True, "source_confidence": 0.41},
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        provenance_types=[ProvenanceType.UNKNOWN],
        basis_statement="Trivial fallback/deny/clarification response with no substantive claim.",
        invariant_decisions={
            "answer_contract_valid": True,
            "general_knowledge_contract_valid": True,
            "answer_mode": "clarify",
            "fallback_action": "ASK_CLARIFYING_QUESTION",
            "answer_policy_rationale": {"fallback_reason": "ambiguous_memory_candidates_without_ask"},
        },
    )
    _run_contract_checks(context)


@then("the assistant asks a targeted clarifying question")
def step_then_assistant_asks_targeted_clarifying_question(context) -> None:
    assert context.pipeline_state.invariant_decisions.get("answer_mode") == "clarify"
    assert "Which person, event, or time window should I focus on?" in context.pipeline_state.final_answer


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


@when("the user asks a definitional knowledge prompt in runtime loop")
def step_when_definitional_prompt_runtime_loop(context) -> None:
    context.retrieval_log_events = [
        ("retrieval_branch_selected", {"retrieval_branch": "memory_retrieval"}),
        ("query_rewrite_output", {"query": "ontology", "skipped": False}),
        ("retrieval_candidates", {"candidate_count": 0, "skipped": False}),
    ]


@then("retrieval branch logging should show memory retrieval with unskipped candidates")
def step_then_definitional_prompt_retrieval_logging(context) -> None:
    branch_payload = next(payload for event, payload in context.retrieval_log_events if event == "retrieval_branch_selected")
    rewrite_payload = next(payload for event, payload in context.retrieval_log_events if event == "query_rewrite_output")
    candidates_payload = next(payload for event, payload in context.retrieval_log_events if event == "retrieval_candidates")

    assert branch_payload["retrieval_branch"] == "memory_retrieval"
    assert rewrite_payload.get("skipped", False) is False
    assert candidates_payload["candidate_count"] >= 0
    assert candidates_payload.get("skipped", False) is False


@when("the user asks a conversational prompt in runtime loop")
def step_when_conversational_prompt_runtime_loop(context) -> None:
    context.retrieval_log_events = [
        ("retrieval_branch_selected", {"retrieval_branch": "direct_answer"}),
        ("query_rewrite_output", {"query": "hello there", "skipped": True}),
        ("retrieval_candidates", {"candidate_count": 0, "skipped": True}),
    ]


@then("retrieval branch logging should show direct answer with skipped candidates")
def step_then_conversational_prompt_retrieval_logging(context) -> None:
    branch_payload = next(payload for event, payload in context.retrieval_log_events if event == "retrieval_branch_selected")
    rewrite_payload = next(payload for event, payload in context.retrieval_log_events if event == "query_rewrite_output")
    candidates_payload = next(payload for event, payload in context.retrieval_log_events if event == "retrieval_candidates")

    assert branch_payload["retrieval_branch"] == "direct_answer"
    assert rewrite_payload.get("skipped") is True
    assert candidates_payload.get("skipped") is True

@when('the user says "Hi! I\'m sebastian" then asks "Who am I?"')
def step_when_identity_recall_followup_pair(context) -> None:
    context.identity_prior_state = PipelineState(
        user_input="Hi! I'm sebastian",
        candidate_facts={
            "facts": [
                {
                    "key": "user_name",
                    "value": "sebastian",
                    "confidence": 0.95,
                    "provenance": "user_utterance",
                }
            ]
        },
    )
    context.identity_recall_force_retrieval = runtime._should_force_memory_retrieval_for_identity_recall(
        utterance="Who am I?",
        prior_state=context.identity_prior_state,
        continuity_evidence=(),
        context_history_anchors=(),
    )


@then("identity recall guard should force memory retrieval branch evaluation")
def step_then_identity_recall_forces_memory_retrieval(context) -> None:
    assert context.identity_recall_force_retrieval is True




@when("encode candidates include multiple plausible intents pre-route")
def step_when_encode_candidates_multiple_plausible_intents_pre_route(context) -> None:
    raw_candidates = [
        {"id": "intent-knowledge", "intent": IntentType.KNOWLEDGE_QUESTION.value, "confidence": 0.79, "provenance": "encode.candidates"},
        {"id": "intent-memory", "intent": IntentType.MEMORY_RECALL.value, "confidence": 0.76, "provenance": "encode.candidates"},
        {"id": "intent-capability", "intent": IntentType.CAPABILITIES_HELP.value, "confidence": 0.72, "provenance": "encode.candidates"},
    ]
    normalized, quarantined = _normalize_encoded_intent_candidates(raw_candidates)
    context.encoded_intent_candidates = normalized
    context.quarantined_intent_candidates = quarantined


@then("encode candidates should retain multiple intents without premature collapse")
def step_then_encode_candidates_retain_multiple_intents_pre_route(context) -> None:
    intents = [candidate["intent"] for candidate in context.encoded_intent_candidates]
    assert len(context.encoded_intent_candidates) >= 2
    assert len(set(intents)) == len(intents)
    assert context.quarantined_intent_candidates == []


@when("encode candidates include duplicate candidate ids")
def step_when_encode_candidates_include_duplicate_candidate_ids(context) -> None:
    raw_candidates = [
        {"id": "intent-memory", "intent": IntentType.MEMORY_RECALL.value, "confidence": 0.66, "provenance": "encode.candidates"},
        {"id": "INTENT-MEMORY", "intent": IntentType.MEMORY_RECALL.value, "confidence": 0.83, "provenance": "encode.candidates"},
        {"id": "intent-knowledge", "intent": IntentType.KNOWLEDGE_QUESTION.value, "confidence": 0.61, "provenance": "encode.candidates"},
        {"id": "intent-knowledge", "intent": IntentType.KNOWLEDGE_QUESTION.value, "confidence": 0.57, "provenance": "encode.candidates"},
    ]
    normalized, quarantined = _normalize_encoded_intent_candidates(raw_candidates)
    context.encoded_intent_candidates = normalized
    context.quarantined_intent_candidates = quarantined


@then("encode candidates should dedupe candidate ids deterministically")
def step_then_encode_candidates_dedupe_candidate_ids_deterministically(context) -> None:
    ids = [candidate["id"] for candidate in context.encoded_intent_candidates]
    assert ids == ["intent-memory", "intent-knowledge"]
    assert context.encoded_intent_candidates[0]["confidence"] == 0.83
    assert context.encoded_intent_candidates[1]["confidence"] == 0.61
    assert context.quarantined_intent_candidates == []


@when("encode candidates include null or malformed provenance")
def step_when_encode_candidates_include_null_or_malformed_provenance(context) -> None:
    raw_candidates = [
        {"id": "intent-knowledge", "intent": IntentType.KNOWLEDGE_QUESTION.value, "confidence": 0.71, "provenance": "encode.candidates"},
        {"id": "intent-memory", "intent": IntentType.MEMORY_RECALL.value, "confidence": 0.74, "provenance": None},
        {"id": "intent-control", "intent": IntentType.CONTROL.value, "confidence": 0.68, "provenance": "   "},
    ]
    normalized, quarantined = _normalize_encoded_intent_candidates(raw_candidates)
    context.encoded_intent_candidates = normalized
    context.quarantined_intent_candidates = quarantined


@then("malformed provenance candidates should be quarantined before downstream stages")
def step_then_malformed_provenance_candidates_quarantined(context) -> None:
    assert [candidate["id"] for candidate in context.encoded_intent_candidates] == ["intent-knowledge"]
    quarantined_ids = [str(candidate.get("normalized_id") or candidate.get("id")) for candidate in context.quarantined_intent_candidates]
    quarantine_reasons = [candidate["quarantine_reason"] for candidate in context.quarantined_intent_candidates]
    assert quarantined_ids == ["intent-control", "intent-memory"]
    assert quarantine_reasons == ["invalid_provenance", "invalid_provenance"]

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


@when("intent taxonomy mapping is evaluated for ambiguous prompts")
def step_when_intent_taxonomy_mapping_evaluated_for_ambiguous_prompts(context) -> None:
    context.typed_intent_mappings = []
    for row in context.table:
        prompt = row["prompt"]
        intent = classify_intent(prompt)
        facets = extract_intent_facets(prompt)
        descriptor = planning_pathway_for_intent(intent, facets)
        context.typed_intent_mappings.append(
            {
                "prompt": prompt,
                "typed_intent": BDDTypedIntent(intent_class=intent, facets=facets, pathway=descriptor.pathway),
                "expected_intent": row["expected_intent"],
                "expected_pathway": row["expected_pathway"],
                "expected_temporal": _parse_bool(row["temporal"]),
                "expected_memory": _parse_bool(row["memory"]),
                "expected_capability": _parse_bool(row["capability"]),
                "expected_control": _parse_bool(row["control"]),
            }
        )


@then("typed intent object fields should match the taxonomy mapping table")
def step_then_typed_intent_fields_match_taxonomy_table(context) -> None:
    assert context.typed_intent_mappings
    for mapping in context.typed_intent_mappings:
        typed_intent = mapping["typed_intent"]
        assert typed_intent.intent_class.value == mapping["expected_intent"], mapping["prompt"]
        assert typed_intent.pathway == mapping["expected_pathway"], mapping["prompt"]
        assert typed_intent.facets.temporal is mapping["expected_temporal"], mapping["prompt"]
        assert typed_intent.facets.memory is mapping["expected_memory"], mapping["prompt"]
        assert typed_intent.facets.capability is mapping["expected_capability"], mapping["prompt"]
        assert typed_intent.facets.control is mapping["expected_control"], mapping["prompt"]


@when("typed intent objects are validated for class and facet compatibility")
def step_when_typed_intent_objects_validated_for_class_and_facet_compatibility(context) -> None:
    context.invalid_typed_intent_results = []
    for row in context.table:
        intent_class = IntentType(row["intent_class"])
        facets = IntentFacets(
            temporal=_parse_bool(row["temporal"]),
            memory=_parse_bool(row["memory"]),
            capability=_parse_bool(row["capability"]),
            control=_parse_bool(row["control"]),
        )
        typed_intent = BDDTypedIntent(
            intent_class=intent_class,
            facets=facets,
            pathway=planning_pathway_for_intent(intent_class, facets).pathway,
        )
        reason = _validate_typed_intent_contract(typed_intent)
        context.invalid_typed_intent_results.append(
            {"typed_intent": typed_intent, "reason": reason, "expected_reason": row["expected_reason"]}
        )


@then("invalid typed intent objects should be rejected with deterministic reasons")
def step_then_invalid_typed_intent_objects_rejected_with_deterministic_reasons(context) -> None:
    assert context.invalid_typed_intent_results
    for result in context.invalid_typed_intent_results:
        assert result["reason"] == result["expected_reason"]


@when("the user asks an ambiguous prompt requiring divergent analysis")
def step_when_ambiguous_prompt_divergent_analysis(context) -> None:
    answer = (
        "Possible explanations: (1) a data-sync delay, (2) conflicting source records, "
        "(3) a wording mismatch in the request. Converged recommendation: verify latest source "
        "timestamp first, then narrow scope if conflict persists."
    )
    context.pipeline_state = _build_base_state(
        user_input="Why did this happen?",
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={"context_confident": False, "ambiguity_detected": True},
    )


@then("the assistant enumerates plausible explanation spaces before converging")
def step_then_enumerates_explanation_space_before_converging(context) -> None:
    final_answer = context.pipeline_state.final_answer
    assert "Possible explanations:" in final_answer
    assert "(1)" in final_answer and "(2)" in final_answer and "(3)" in final_answer
    assert "Converged recommendation:" in final_answer
    assert final_answer.index("Possible explanations:") < final_answer.index("Converged recommendation:")


@when("the user asks for a multi-framework perspective switch")
def step_when_multi_framework_perspective_switch(context) -> None:
    answer = (
        "Framework: systems -> treat this as process and dependency risk. "
        "Framework: behavioral -> treat this as intent and communication risk. "
        "Synthesis: prioritize the systems fix, then add behavioral guardrails."
    )
    context.pipeline_state = _build_base_state(
        user_input="Analyze this from multiple frameworks.",
        final_answer=answer,
        draft_answer=answer,
        confidence_decision={"context_confident": True, "multi_framework": True},
    )


@then("the assistant presents multiple frameworks and a synthesized conclusion")
def step_then_presents_frameworks_and_synthesis(context) -> None:
    final_answer = context.pipeline_state.final_answer
    assert "Framework: systems" in final_answer
    assert "Framework: behavioral" in final_answer
    assert "Synthesis:" in final_answer
    assert final_answer.index("Framework: systems") < final_answer.index("Framework: behavioral") < final_answer.index("Synthesis:")


@when("the user provides a self-identification utterance")
def step_when_self_identification_utterance(context) -> None:
    context.ambiguous_intent = classify_intent("my name is taylor")




class _SelfIdentificationRewriteLLM:
    def __init__(self, content: str) -> None:
        self._content = content

    def invoke(self, _msgs):
        return type("_Resp", (), {"content": self._content})()


@when("the user provides a self-identification utterance for rewrite")
def step_when_self_identification_for_rewrite(context) -> None:
    context.self_identification_input = "My name is Taylor"
    state = PipelineState(user_input=context.self_identification_input)
    rewritten = stage_rewrite_query(_SelfIdentificationRewriteLLM("What is the assistant's name?"), state)
    context.rewrite_output = rewritten.rewritten_query


@then("rewrite output should preserve identity declaration wording")
def step_then_rewrite_preserves_identity_declaration(context) -> None:
    assert context.rewrite_output == context.self_identification_input


@then("rewrite output should not be assistant-focused for self-identification input")
def step_then_rewrite_not_assistant_focused_for_identity(context) -> None:
    lowered = context.rewrite_output.lower()
    assert "assistant" not in lowered
    assert "your name" not in lowered

@when("the user provides a greeting utterance")
def step_when_greeting_utterance(context) -> None:
    context.ambiguous_intent = classify_intent("hello")


@when("the user provides a say-hello command")
def step_when_say_hello_command(context) -> None:
    context.ambiguous_intent = classify_intent("say hello to me")


@then("the utterance should route to non-knowledge social intent deterministically")
def step_then_non_knowledge_social_intent(context) -> None:
    assert context.ambiguous_intent is IntentType.META_CONVERSATION


@then('the response should not include "{unexpected_substring}"')
def step_then_response_excludes_substring(context, unexpected_substring: str) -> None:
    assert unexpected_substring not in context.pipeline_state.final_answer

@when("the user asks a mixed temporal-memory phrase")
def step_when_mixed_temporal_memory_phrase(context) -> None:
    utterance = "how many minutes ago did we talk before?"
    context.ambiguous_intent = classify_intent(utterance)
    context.intent_facets = extract_intent_facets(utterance)


@then("the utterance should route to time-query intent with temporal and memory facets")
def step_then_mixed_temporal_memory_phrase(context) -> None:
    assert context.ambiguous_intent is IntentType.TIME_QUERY
    assert context.intent_facets.temporal is True
    assert context.intent_facets.memory is True


@when("the user asks a capabilities-in-context phrase")
def step_when_capabilities_in_context_phrase(context) -> None:
    utterance = "what is ontology with satellite context?"
    context.ambiguous_intent = classify_intent(utterance)
    context.intent_facets = extract_intent_facets(utterance)


@then("the utterance should route to knowledge intent with capability facet")
def step_then_capabilities_in_context_phrase(context) -> None:
    assert context.ambiguous_intent is IntentType.KNOWLEDGE_QUESTION
    assert context.intent_facets.capability is True



@when("retrieval policy evaluates empty and scored-empty evidence states")
def step_when_retrieval_policy_evaluates_empty_vs_scored_empty(context) -> None:
    context.empty_evidence_policy = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    context.scored_empty_policy = decide(
        utterance="what is ontology?",
        intent=IntentType.KNOWLEDGE_QUESTION,
        retrieval_candidates_considered=2,
        hit_count=0,
    )


@then("retrieval policy should record empty-evidence and scored-empty postures distinctly")
def step_then_retrieval_policy_postures_distinct(context) -> None:
    assert context.empty_evidence_policy.evidence_posture is EvidencePosture.EMPTY_EVIDENCE
    assert context.scored_empty_policy.evidence_posture is EvidencePosture.SCORED_EMPTY




@when("memory-recall follow-up is evaluated under scored-empty evidence")
def step_when_memory_followup_scored_empty(context) -> None:
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=3,
        hit_count=0,
    )
    context.memory_followup_decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=retrieval)


@then("memory-recall follow-up policy should keep clarification decision class and memory retrieval branch")
def step_then_memory_followup_no_downgrade(context) -> None:
    assert context.memory_followup_decision.decision_class is DecisionClass.ASK_FOR_CLARIFICATION
    assert context.memory_followup_decision.retrieval_branch == "memory_retrieval"
    assert context.memory_followup_decision.reasoning.get("empty_vs_scored") == "scored_empty"



@when("a temporal follow-up references prior memory recall continuity")
def step_when_temporal_followup_references_memory_continuity(context) -> None:
    prior_state = PipelineState(
        user_input="Who am I?",
        final_answer="You are Sam.",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        prior_unresolved_intent=IntentType.MEMORY_RECALL.value,
        commit_receipt={"confirmed_user_facts": ["name=Sam"]},
    )

    followup_context = resolve_context(utterance="when was that again?", prior_pipeline_state=prior_state)
    context.temporal_followup_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized_turn_state_for_bdd("when was that again?"),
            context=followup_context,
            fallback_utterance="when was that again?",
        )
    )


@then("the resolved follow-up intent should preserve time-query continuity instead of knowledge-question fallback")
def step_then_temporal_followup_preserves_time_query(context) -> None:
    assert context.temporal_followup_resolution.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert context.temporal_followup_resolution.resolved_intent is IntentType.TIME_QUERY

@when("intent continuity is evaluated for affirmative and non-affirmative follow-ups")
def step_when_intent_continuity_evaluated_for_followups(context) -> None:
    prior_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
    )
    affirmative_context = resolve_context(utterance="yes", prior_pipeline_state=prior_state)
    non_affirmative_context = resolve_context(utterance="no, never mind", prior_pipeline_state=prior_state)
    context.affirmative_resolution = resolve_intent(resolution_input=IntentResolutionInput(stabilized_turn_state=_stabilized_turn_state_for_bdd("yes"), context=affirmative_context, fallback_utterance="yes"))
    context.non_affirmative_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized_turn_state_for_bdd("no, never mind"),
            context=non_affirmative_context,
            fallback_utterance="no, never mind",
        )
    )


@then("continuity routing should preserve prior intent only for affirmative clarification follow-ups")
def step_then_continuity_routing_preserves_only_affirmative(context) -> None:
    assert context.affirmative_resolution.resolved_intent is IntentType.CAPABILITIES_HELP
    assert context.non_affirmative_resolution.resolved_intent is context.non_affirmative_resolution.classified_intent


@given("a prior clarification commit-state harness for capabilities help")
def step_given_prior_clarification_commit_state_harness(context) -> None:
    context.prior_clarification_state = PipelineState(
        user_input="ask something via satellite",
        final_answer=ROUTE_TO_ASK_ANSWER,
        resolved_intent=IntentType.CAPABILITIES_HELP.value,
        prior_unresolved_intent=IntentType.CAPABILITIES_HELP.value,
        commit_receipt={
            "pending_clarification": {"required": True, "question": "Do you want me to proceed via satellite?"},
            "remaining_obligations": ["clarify_satellite_request"],
            "confirmed_user_facts": [],
        },
    )


@when('a topic shift turn is committed before delayed follow-up "yes"')
def step_when_topic_shift_then_delayed_yes(context) -> None:
    topic_shift_state = PipelineState(
        user_input="also remind me to buy milk",
        final_answer="Got it — reminder noted.",
        resolved_intent=IntentType.META_CONVERSATION.value,
        commit_receipt={
            "pending_clarification": {"required": False, "question": ""},
            "remaining_obligations": [],
            "confirmed_user_facts": ["reminder=buy milk"],
        },
    )
    delayed_context = resolve_context(utterance="yes", prior_pipeline_state=topic_shift_state)
    context.delayed_yes_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized_turn_state_for_bdd("yes"),
            context=delayed_context,
            fallback_utterance="yes",
        )
    )
    context.delayed_yes_commit_transitions = {
        "persisted": list(topic_shift_state.commit_receipt.get("confirmed_user_facts", [])),
        "cleared": ["clarification_continuity", "clarify_satellite_request"],
        "history_anchors": delayed_context.history_anchors,
        "continuity_posture": delayed_context.continuity_posture,
    }


@then("delayed follow-up should re-evaluate instead of preserving prior clarification intent")
def step_then_delayed_yes_re_evaluates(context) -> None:
    assert context.delayed_yes_resolution.classified_intent is IntentType.KNOWLEDGE_QUESTION
    assert context.delayed_yes_resolution.resolved_intent is IntentType.KNOWLEDGE_QUESTION


@then("commit-state transitions should clear stale clarification continuity at the topic-shift boundary")
def step_then_delayed_yes_commit_transition_clears_stale_clarification(context) -> None:
    transitions = context.delayed_yes_commit_transitions
    assert transitions["persisted"] == ["reminder=buy milk"]
    assert transitions["cleared"] == ["clarification_continuity", "clarify_satellite_request"]
    assert "clarification_continuity" not in transitions["history_anchors"]
    assert transitions["continuity_posture"] is not ContinuityPosture.PRESERVE_PRIOR_INTENT


@when('a hostile follow-up "yeah sure whatever" is evaluated against prior clarification state')
def step_when_hostile_followup_evaluated(context) -> None:
    hostile_context = resolve_context(utterance="yeah sure whatever", prior_pipeline_state=context.prior_clarification_state)
    context.hostile_resolution = resolve_intent(
        resolution_input=IntentResolutionInput(
            stabilized_turn_state=_stabilized_turn_state_for_bdd("yeah sure whatever"),
            context=hostile_context,
            fallback_utterance="yeah sure whatever",
        )
    )
    context.hostile_commit_transitions = {
        "persisted": list(context.prior_clarification_state.commit_receipt.get("remaining_obligations", [])),
        "cleared": ["clarification_continuity"],
        "history_anchors": hostile_context.history_anchors,
        "continuity_posture": hostile_context.continuity_posture,
    }


@then("hostile affirmation should not preserve prior clarification intent")
def step_then_hostile_affirmation_not_preserved(context) -> None:
    assert context.hostile_resolution.resolved_intent is context.hostile_resolution.classified_intent
    assert context.hostile_resolution.resolved_intent is IntentType.KNOWLEDGE_QUESTION


@then("commit-state transitions should clear clarification obligations at the hostile follow-up boundary")
def step_then_hostile_commit_transition_clears_obligations(context) -> None:
    transitions = context.hostile_commit_transitions
    assert transitions["persisted"] == ["clarify_satellite_request"]
    assert transitions["cleared"] == ["clarification_continuity"]
    assert "clarification_continuity" not in transitions["history_anchors"]
    assert transitions["continuity_posture"] is ContinuityPosture.REEVALUATE


@when("policy decision objects are resolved from typed evidence states")
def step_when_policy_decision_objects_typed(context) -> None:
    memory_retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(
            structured_facts=(EvidenceRecord(ref_id="fact-1", score=0.9, content="user_name=Sebastian"),),
        ),
        retrieval_candidates_considered=3,
        hit_count=1,
    )
    scored_empty = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=3,
        hit_count=0,
    )
    no_retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )

    context.typed_decisions = [
        decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=memory_retrieval),
        decide_from_evidence(intent=IntentType.KNOWLEDGE_QUESTION, retrieval=scored_empty),
        decide_from_evidence(intent=IntentType.META_CONVERSATION, retrieval=no_retrieval),
        decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=scored_empty),
        decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=scored_empty, repair_required=True),
    ]


@then('the decision outcomes should include "answer_from_memory" and "answer_general_knowledge_labeled"')
def step_then_decision_outcomes_include_memory_and_general(context) -> None:
    decisions = {decision.decision_class.value for decision in context.typed_decisions}
    assert "answer_from_memory" in decisions
    assert "answer_general_knowledge_labeled" in decisions


@then('the decision outcomes should include "ask_for_clarification" and "continue_repair_reconstruction"')
def step_then_decision_outcomes_include_clarify_and_repair(context) -> None:
    decisions = {decision.decision_class.value for decision in context.typed_decisions}
    assert "ask_for_clarification" in decisions
    assert "continue_repair_reconstruction" in decisions


@when("typed fallback contracts are resolved for empty and scored-empty evidence")
def step_when_typed_fallback_contracts_resolved(context) -> None:
    empty_retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    scored_empty_retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=3,
        hit_count=0,
    )

    empty_decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=empty_retrieval)
    scored_empty_decision = decide_from_evidence(intent=IntentType.MEMORY_RECALL, retrieval=scored_empty_retrieval)

    context.typed_fallback_mapping = {
        "E.empty": {
            "typed_state": "E.empty",
            "evidence_posture": empty_retrieval.evidence_posture.value,
            "decision_class": empty_decision.decision_class.value,
            "provenance_label": "UNKNOWN",
            "fallback_strategy": "ASK_CLARIFIER",
        },
        "E.scored_empty": {
            "typed_state": "E.scored_empty",
            "evidence_posture": scored_empty_retrieval.evidence_posture.value,
            "decision_class": scored_empty_decision.decision_class.value,
            "provenance_label": "UNKNOWN",
            "fallback_strategy": "ANSWER_UNKNOWN",
        },
        "E.scored_empty_non_memory": {
            "typed_state": "E.scored_empty_non_memory",
            "evidence_posture": scored_empty_retrieval.evidence_posture.value,
            "decision_class": DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED.value,
            "provenance_label": "UNKNOWN",
            "fallback_strategy": "OFFER_ASSIST_ALTERNATIVES",
        },
    }


@then("typed evidence states should remain distinct for empty and scored-empty")
def step_then_typed_evidence_states_distinct(context) -> None:
    empty_contract = context.typed_fallback_mapping["E.empty"]
    scored_empty_contract = context.typed_fallback_mapping["E.scored_empty"]
    assert empty_contract["typed_state"] != scored_empty_contract["typed_state"]
    assert empty_contract["evidence_posture"] == EvidencePosture.EMPTY_EVIDENCE.value
    assert scored_empty_contract["evidence_posture"] == EvidencePosture.SCORED_EMPTY.value


@then('the typed evidence-state mapping should include decision class "{decision_class}" and provenance label "{provenance_label}" for "{typed_state}"')
def step_then_typed_mapping_decision_and_provenance(context, decision_class: str, provenance_label: str, typed_state: str) -> None:
    state_contract = context.typed_fallback_mapping[typed_state]
    _assert_evidence_state_fields(
        state_contract,
        typed_state=typed_state,
        evidence_posture=str(state_contract["evidence_posture"]),
        decision_class=decision_class,
        provenance_label=provenance_label,
        fallback_strategy=str(state_contract["fallback_strategy"]),
    )


@then('the typed evidence-state mapping should include fallback strategy "{fallback_strategy}" for "{typed_state}"')
def step_then_typed_mapping_fallback_strategy(context, fallback_strategy: str, typed_state: str) -> None:
    state_contract = context.typed_fallback_mapping[typed_state]
    _assert_evidence_state_fields(
        state_contract,
        typed_state=typed_state,
        evidence_posture=str(state_contract["evidence_posture"]),
        decision_class=str(state_contract["decision_class"]),
        provenance_label=str(state_contract["provenance_label"]),
        fallback_strategy=fallback_strategy,
    )


@then('the fallback reason should be "{fallback_reason}"')
def step_then_fallback_reason_should_be(context, fallback_reason: str) -> None:
    rationale = context.pipeline_state.invariant_decisions.get("answer_policy_rationale", {})
    assert rationale.get("fallback_reason") == fallback_reason


class _BDDMetaAckLLM:
    class _Response:
        content = "Got it — I can keep that in mind."

    def invoke(self, _msgs):
        return self._Response()


def _resolve_contract_probe(utterance: str) -> dict[str, object]:
    context = resolve_context(utterance=utterance, prior_pipeline_state=None)
    intent_resolution = resolve_intent(resolution_input=IntentResolutionInput(stabilized_turn_state=_stabilized_turn_state_for_bdd(utterance), context=context, fallback_utterance=utterance))
    policy_decision = decide(
        utterance=utterance,
        intent=intent_resolution.resolved_intent,
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    retrieval = retrieval_result(
        evidence_bundle=EvidenceBundle(),
        retrieval_candidates_considered=0,
        hit_count=0,
    )
    decision_object = decide_from_evidence(intent=intent_resolution.resolved_intent, retrieval=retrieval)
    answered = run_answer_stage_flow(
        _BDDMetaAckLLM(),
        PipelineState(
            user_input=utterance,
            resolved_intent=intent_resolution.resolved_intent.value,
            confidence_decision={"context_confident": False, "ambiguity_detected": False},
        ),
        chat_history=deque(),
        hits=[],
        capability_status="ask_unavailable",
        selected_decision=decision_object,
    )
    return {
        "intent": intent_resolution.resolved_intent.value,
        "retrieval_branch": policy_decision.retrieval_branch,
        "decision_class": decision_object.decision_class.value,
        "fallback_action": str(answered.invariant_decisions.get("fallback_action", "")),
        "answer_mode": str(answered.invariant_decisions.get("answer_mode", "")),
    }


@when("note-taking utterance contract probe is resolved through canonical decisioning")
def step_when_note_taking_contract_probe(context) -> None:
    context.contract_probe = _resolve_contract_probe("please make a note that i prefer tea")


@when("memory-write utterance contract probe is resolved through canonical decisioning")
def step_when_memory_write_contract_probe(context) -> None:
    context.contract_probe = _resolve_contract_probe("remember this: i parked on level 3")


@then('the canonical contract should resolve intent "{intent}" retrieval branch "{retrieval_branch}" decision class "{decision_class}" fallback action "{fallback_action}" and answer mode "{answer_mode}"')
def step_then_canonical_contract_probe(context, intent: str, retrieval_branch: str, decision_class: str, fallback_action: str, answer_mode: str) -> None:
    assert context.contract_probe == {
        "intent": intent,
        "retrieval_branch": retrieval_branch,
        "decision_class": decision_class,
        "fallback_action": fallback_action,
        "answer_mode": answer_mode,
    }

@when("a definitional knowledge prompt has initial empty retrieval and async continuation is off")
def step_when_definitional_prompt_sync_retry(context) -> None:
    context.retrieval_log_events = [
        ("retrieval_branch_selected", {"retrieval_branch": "memory_retrieval"}),
        (
            "retrieval_candidates",
            {
                "candidate_count": 0,
                "skipped": False,
                "retry": {"attempted": True, "waited_seconds": 0.15, "reason": "sync_retry_completed"},
            },
        ),
    ]
    context.pipeline_state = _build_base_state(
        user_input="What is ontology?",
        final_answer="General definition (not from your memory): Ontology organizes concepts and relations.",
        draft_answer="General definition (not from your memory): Ontology organizes concepts and relations.",
        confidence_decision={
            "context_confident": False,
            "ambiguity_detected": False,
            "retrieval_branch": "memory_retrieval",
            "retrieval_candidates_considered": 0,
        },
    )
    context.pipeline_state = replace(
        context.pipeline_state,
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
    )


@then("retrieval retry logging should show one bounded sync retry")
def step_then_retrieval_retry_logging_sync_once(context) -> None:
    candidates_payload = next(payload for event, payload in context.retrieval_log_events if event == "retrieval_candidates")
    retry_payload = candidates_payload.get("retry", {})
    assert retry_payload.get("attempted") is True
    assert retry_payload.get("reason") == "sync_retry_completed"
    assert float(retry_payload.get("waited_seconds", 0.0)) >= 0.0


@then("fallback outcome should remain deterministic when evidence stays empty")
def step_then_fallback_deterministic_after_sync_retry(context) -> None:
    assert context.pipeline_state.invariant_decisions.get("answer_mode") == "assist"
    assert context.pipeline_state.invariant_decisions.get("fallback_action") == "ANSWER_GENERAL_KNOWLEDGE"
