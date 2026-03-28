from __future__ import annotations

import uuid
import warnings
from collections import deque
from dataclasses import dataclass, replace
import re

import arrow
from langchain_core.documents import Document
from langchain_ollama import ChatOllama

from testbot.answer_policy import AnswerRoutingDecision, resolve_answer_mode
from testbot.clock import Clock, SystemClock
from testbot.history_packer import pack_chat_history, render_packed_history
from testbot.intent_router import (
    IntentType,
    extract_intent_facets,
    is_satellite_action_request,
    planning_pathway_for_intent,
)
from testbot.logic.alignment import (
    assess_general_knowledge_contract,
    has_general_knowledge_marker,
    has_required_memory_citation,
    is_non_trivial_answer,
    is_unsafe_user_request,
    passes_general_knowledge_confidence_gate,
    raw_claim_like_text_detected,
    validate_answer_contract,
)
from testbot.pipeline_state import PipelineState, ProvenanceType
from testbot.policy_decision import DecisionClass, DecisionObject
from testbot.reflection_policy import CapabilityStatus
from testbot.response_planner import build_response_plan, render_response_plan_block
from testbot.runtime_capability_service import (
    CapabilitySnapshotData as CapabilitySnapshot,
    RuntimeCapabilityStatusData as RuntimeCapabilityStatus,
)
from testbot.evidence_retrieval import RetrievalInputRecord
from testbot.time_reasoning import elapsed_since_last_user_message, resolve_relative_date
from testbot.logic.decision_helpers import (
    decision_object_from_assembled as _decision_object_from_fallback_action,
    resolve_answer_routing_for_stage as _resolve_answer_routing_for_stage_service,
    resolve_answer_routing_from_decision_object as _resolve_answer_routing_from_decision_object_service,
    selected_decision_from_confidence as _selected_decision_from_confidence_service,
)

ChatMsg = dict[str, str]


_CAPABILITY_OFFER_PATTERN = re.compile(
    r"\b("
    r"i can look up|"
    r"i can find|"
    r"i can search|"
    r"i can help you find|"
    r"would you like me to|"
    r"i can define|"
    r"i can look that up|"
    r"i can either\b[^.?!]*\bor\b|"
    r"suggest where to check next|"
    r"suggest a quick way to verify|"
    r"offer a best-effort response|"
    r"help you reconstruct the timeline"
    r")\b",
    re.IGNORECASE,
)


def detect_capability_offer(text: str) -> str:
    if _CAPABILITY_OFFER_PATTERN.search(text or ""):
        return "capability_offer"
    return ""


def answer_assemble_for_turn_service(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[RetrievalInputRecord],
    capability_status: CapabilityStatus,
    answer_routing: AnswerRoutingDecision,
    runtime_capability_status: RuntimeCapabilityStatus | None = None,
    clock: Clock | None = None,
    document_from_retrieval_input,
    render_context,
    answer_prompt,
    build_partial_memory_clarifier,
    append_session_log,
    deny_answer: str,
    route_to_ask_answer: str,
    assist_alternatives_answer: str,
    fallback_answer: str,
    non_knowledge_uncertainty_answer: str,
) -> AnswerAssembleResult:
    docs = [document_from_retrieval_input(record) for record in hits]
    return answer_assemble(
        llm,
        state,
        chat_history=chat_history,
        hits=docs,
        capability_status=capability_status,
        answer_routing=answer_routing,
        runtime_capability_status=runtime_capability_status,
        clock=clock,
        timezone="Europe/Helsinki",
        render_context=render_context,
        answer_prompt=answer_prompt,
        build_partial_memory_clarifier=build_partial_memory_clarifier,
        append_session_log=append_session_log,
        deny_answer=deny_answer,
        route_to_ask_answer=route_to_ask_answer,
        assist_alternatives_answer=assist_alternatives_answer,
        fallback_answer=fallback_answer,
        non_knowledge_uncertainty_answer=non_knowledge_uncertainty_answer,
    )


def answer_validate_for_turn_service(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    hits: list[RetrievalInputRecord],
    chat_history: deque[ChatMsg],
    pending_lookup_override: bool | None = None,
    document_from_retrieval_input,
    build_provenance_metadata,
    evaluate_alignment_decision,
    fallback_answer: str,
    deny_answer: str,
    assist_alternatives_answer: str,
    non_knowledge_uncertainty_answer: str,
    clarify_answer: str,
    route_to_ask_answer: str,
) -> AnswerValidateResult:
    docs = [document_from_retrieval_input(record) for record in hits]
    return answer_validate(
        state,
        assembled=assembled,
        hits=docs,
        chat_history=chat_history,
        pending_lookup_override=pending_lookup_override,
        build_provenance_metadata=build_provenance_metadata,
        evaluate_alignment_decision=evaluate_alignment_decision,
        fallback_answer=fallback_answer,
        deny_answer=deny_answer,
        assist_alternatives_answer=assist_alternatives_answer,
        non_knowledge_uncertainty_answer=non_knowledge_uncertainty_answer,
        clarify_answer=clarify_answer,
        route_to_ask_answer=route_to_ask_answer,
    )


@dataclass(frozen=True)
class AnswerAssembleResult:
    draft_answer: str
    final_answer: str
    fallback_action: str
    intent_class: str
    social_or_non_knowledge_intent: bool
    answer_policy_rationale: dict[str, object]
    capability_help_short_circuit: bool = False


@dataclass(frozen=True)
class AnswerValidateResult:
    final_answer: str
    claims: list[str]
    provenance_types: list[ProvenanceType]
    used_memory_refs: list[str]
    used_source_evidence_refs: list[str]
    source_evidence_attribution: list[dict[str, str]]
    basis_statement: str
    invariant_decisions: dict[str, object]
    alignment_decision: dict[str, object]


def intent_class_for_policy(intent: IntentType) -> str:
    if intent == IntentType.MEMORY_RECALL:
        return "memory_recall"
    if intent == IntentType.TIME_QUERY:
        return "time_query"
    return "non_memory"


def is_social_or_non_knowledge_intent(intent: IntentType) -> bool:
    return intent in {IntentType.META_CONVERSATION, IntentType.CONTROL, IntentType.CAPABILITIES_HELP}


def is_capabilities_help_request(intent: IntentType) -> bool:
    return intent == IntentType.CAPABILITIES_HELP


def format_capabilities_help_answer(*, status: RuntimeCapabilityStatus, capability_status: CapabilityStatus) -> str:
    ask_available = capability_status == "ask_available"

    def _derive_core_reasoning_lines() -> list[str]:
        memory_text = (
            f"- Memory recall: available. can recall stored memory cards using the '{status.memory_backend}' backend; "
            "cannot invent details that are not in memory."
        )
        general_state = "available" if status.ollama_available else "unavailable"
        general_text = (
            f"- Grounded explanations: {general_state}. can provide grounded explanations when Ollama is reachable; "
            "cannot generate model-based explanations while Ollama is unavailable."
        )
        return ["core_reasoning:", memory_text, general_text]

    def _derive_interaction_lines() -> list[str]:
        if status.effective_mode == "cli":
            if status.text_clarification_available:
                clarification_state = "available"
                clarification_text = (
                    f"- Clarification/disambiguation: {clarification_state}. text clarification still available in CLI when memory is incomplete; "
                    "interactive satellite ask flow unavailable in CLI mode."
                )
            else:
                clarification_state = "unavailable"
                clarification_text = (
                    f"- Clarification/disambiguation: {clarification_state}. no clarification path is active in the current runtime; "
                    "interactive satellite ask flow unavailable."
                )
        else:
            clarification_available = ask_available or status.text_clarification_available
            clarification_state = "available" if clarification_available else "unavailable"
            clarification_text = (
                f"- Clarification/disambiguation: {clarification_state}. can ask follow-up questions when an active clarification path exists; "
                "cannot clarify when no clarification path is active."
            )
        satellite_ask_state = "available" if status.satellite_ask_available else "unavailable"
        satellite_ask_text = (
            f"- Satellite ask loop: {satellite_ask_state}. can run interactive satellite ask follow-ups when available; "
            "cannot run satellite ask when Home Assistant satellite flow is unavailable."
        )
        return ["interaction:", clarification_text, satellite_ask_text]

    def _derive_integrations_lines() -> list[str]:
        if status.ha_available and status.effective_mode == "satellite":
            ha_text = (
                "- Home Assistant satellite actions: available. can use satellite speak/start-conversation actions; "
                "cannot act on entities that are missing or unauthorized."
            )
        elif status.ha_available:
            ha_text = (
                "- Home Assistant satellite actions: degraded. can connect to Home Assistant, but current mode is CLI; "
                "cannot run the satellite voice loop until satellite mode is selected."
            )
        else:
            mode_note = "daemon mode blocks fallback" if status.daemon_mode else "CLI fallback is active"
            ha_text = (
                f"- Home Assistant satellite actions: unavailable. can continue in {status.effective_mode} mode ({mode_note}); "
                "cannot run satellite actions while Home Assistant is unavailable."
            )
        return ["integrations:", ha_text]

    def _derive_diagnostics_lines() -> list[str]:
        if status.debug_enabled:
            debug_text = "- Debug visibility: enabled (TESTBOT_DEBUG=1)."
        else:
            debug_text = "- Debug visibility: disabled (set TESTBOT_DEBUG=1 to enable)."
        return ["diagnostics:", debug_text]

    mode_line = (
        f"Runtime mode: requested={status.requested_mode}, effective={status.effective_mode}, "
        f"daemon={status.daemon_mode}, fallback={status.fallback_reason or 'none'}."
    )

    return "\n".join(
        [
            mode_line,
            *_derive_core_reasoning_lines(),
            *_derive_interaction_lines(),
            *_derive_integrations_lines(),
            *_derive_diagnostics_lines(),
            f"policy_hint: reflection capability status={capability_status}.",
        ]
    )


def format_satellite_action_alternatives(*, status: RuntimeCapabilityStatus) -> str:
    mode_hint = "switch to --mode satellite" if status.ha_available else "restore Home Assistant connectivity first"
    return "\n".join(
        [
            "satellite_action_request:",
            "- Requested satellite action: detected.",
            f"- Action alternatives: continue in {status.effective_mode} mode for text Q&A right now; {mode_hint} to re-enable interactive satellite ask.",
            "- Next step: ask your question directly in this chat, or request a capability check after changing runtime mode.",
        ]
    )


def select_memory_recovery_hit(hits: list[Document]) -> Document | None:
    for hit in hits:
        metadata = hit.metadata if isinstance(hit.metadata, dict) else {}
        doc_id = str(metadata.get("doc_id", "")).strip()
        ts = str(metadata.get("ts", "")).strip()
        snippet = (hit.page_content or "").strip()
        if doc_id and ts and snippet:
            return hit
    return None


def build_memory_recall_recovery_answer(hit: Document) -> str:
    metadata = hit.metadata if isinstance(hit.metadata, dict) else {}
    doc_id = str(metadata.get("doc_id", "")).strip()
    ts = str(metadata.get("ts", "")).strip()
    snippet = " ".join((hit.page_content or "").split())
    trimmed_snippet = snippet[:180].rstrip()
    return f"From memory, I found: {trimmed_snippet}. doc_id: {doc_id}, ts: {ts}"


def is_clarification_answer(text: str, *, clarify_answer: str, route_to_ask_answer: str) -> bool:
    normalized = (text or "").strip()
    return normalized in {clarify_answer, route_to_ask_answer} or normalized.startswith(
        "I found related memory fragments ("
    )


def build_time_answer(*, user_input: str, now: arrow.Arrow, last_user_message_ts: str | None, timezone: str) -> str:
    normalized = user_input.strip().lower()

    if "ago" in normalized:
        elapsed_seconds = elapsed_since_last_user_message(last_user_message_ts, now)
        if elapsed_seconds is None:
            return "I don't have a previous user-message timestamp yet."
        minutes = elapsed_seconds // 60
        return f"Your previous user message was {minutes} minute(s) ago."

    for token in ("today", "tomorrow", "yesterday"):
        if token in normalized:
            resolved = resolve_relative_date(token, now, timezone)
            if resolved is not None:
                return f"{token.capitalize()} is {resolved} in {timezone}."

    return "I can answer relative time questions like 'how many minutes ago' or 'what is tomorrow?'."


def answer_assemble(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    answer_routing: AnswerRoutingDecision,
    runtime_capability_status: RuntimeCapabilityStatus | None,
    clock: Clock | None,
    timezone: str,
    render_context,
    answer_prompt,
    build_partial_memory_clarifier,
    append_session_log,
    deny_answer: str,
    route_to_ask_answer: str,
    assist_alternatives_answer: str,
    fallback_answer: str,
    non_knowledge_uncertainty_answer: str,
) -> AnswerAssembleResult:
    runtime_capability_status = runtime_capability_status or RuntimeCapabilityStatus(
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

    fallback_action = answer_routing.fallback_action
    effective_fallback_action = fallback_action
    clarification_allowed = answer_routing.clarification_allowed
    resolved_intent = IntentType(state.resolved_intent or IntentType.KNOWLEDGE_QUESTION.value)
    intent_class = intent_class_for_policy(resolved_intent)
    social_or_non_knowledge = is_social_or_non_knowledge_intent(resolved_intent)
    satellite_action_request = is_satellite_action_request(state.user_input)

    def _fallback_answer_for_action(action: str, *, local_intent_class: str) -> str:
        if action == "ROUTE_TO_ASK":
            return route_to_ask_answer
        if action == "ASK_CLARIFYING_QUESTION":
            if local_intent_class == "memory_recall":
                return build_partial_memory_clarifier(hits)
            return assist_alternatives_answer
        if action == "ANSWER_UNKNOWN":
            return non_knowledge_uncertainty_answer
        if action == "ANSWER_TIME":
            if clock is None:
                return "I can answer relative time questions like 'how many minutes ago' or 'what is tomorrow?'."
            return build_time_answer(
                user_input=state.user_input,
                now=clock.now(),
                last_user_message_ts=state.last_user_message_ts,
                timezone=timezone,
            )
        return assist_alternatives_answer

    if is_capabilities_help_request(resolved_intent):
        final_answer = format_capabilities_help_answer(
            status=runtime_capability_status,
            capability_status=capability_status,
        )
        if (
            satellite_action_request
            and runtime_capability_status.effective_mode == "cli"
            and not runtime_capability_status.satellite_ask_available
        ):
            final_answer = "\n".join(
                [
                    final_answer,
                    format_satellite_action_alternatives(status=runtime_capability_status),
                ]
            )
        return AnswerAssembleResult(
            draft_answer="",
            final_answer=final_answer,
            fallback_action="OFFER_CAPABILITY_ALTERNATIVES",
            intent_class=intent_class,
            social_or_non_knowledge_intent=social_or_non_knowledge,
            answer_policy_rationale={"capability_help_short_circuit": True},
            capability_help_short_circuit=True,
        )

    context_str = render_context(hits)
    history_str = render_packed_history(pack_chat_history(list(chat_history)))
    planning_descriptor = planning_pathway_for_intent(resolved_intent, extract_intent_facets(state.user_input))
    response_plan_block = render_response_plan_block(build_response_plan(
        descriptor=planning_descriptor,
        user_input=state.user_input,
    ))
    msgs = answer_prompt.format_messages(
        input=state.user_input,
        chat_history=history_str,
        context=context_str,
        response_plan=response_plan_block,
    )

    def _clarifier_or_policy_alternative() -> str:
        if clarification_allowed and intent_class == "memory_recall":
            return build_partial_memory_clarifier(hits)
        if intent_class == "time_query":
            return _fallback_answer_for_action("ANSWER_TIME", local_intent_class=intent_class)
        return assist_alternatives_answer

    def _memory_recall_recovery_or_alternative() -> str:
        selected_hit = select_memory_recovery_hit(hits)
        if selected_hit is not None:
            return build_memory_recall_recovery_answer(selected_hit)
        return _clarifier_or_policy_alternative()

    if is_unsafe_user_request(state.user_input):
        draft_answer = ""
        final_answer = deny_answer
    elif fallback_action == "ROUTE_TO_ASK":
        draft_answer = ""
        final_answer = route_to_ask_answer
    elif fallback_action == "ASK_CLARIFYING_QUESTION":
        draft_answer = ""
        final_answer = _clarifier_or_policy_alternative()
        if intent_class == "time_query":
            effective_fallback_action = "ANSWER_TIME"
            draft_answer = final_answer
    elif fallback_action == "ANSWER_UNKNOWN":
        draft_answer = fallback_answer
        final_answer = _fallback_answer_for_action(fallback_action, local_intent_class=intent_class)
    elif fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        draft_answer = ""
        final_answer = assist_alternatives_answer
    elif fallback_action == "ANSWER_TIME":
        final_answer = _fallback_answer_for_action(fallback_action, local_intent_class=intent_class)
        draft_answer = final_answer
    else:
        try:
            draft_answer = (llm.invoke(msgs).content or "").strip()
        except Exception as exc:
            append_session_log(
                "answer_generation_failed",
                {
                    "error_class": type(exc).__name__,
                    "error_message": str(exc),
                    "fallback_action": fallback_action,
                },
            )
            draft_answer = ""
            final_answer = _fallback_answer_for_action(fallback_action, local_intent_class=intent_class)
        else:
            if not draft_answer:
                final_answer = assist_alternatives_answer
            elif validate_answer_contract(draft_answer):
                final_answer = draft_answer
            elif intent_class == "memory_recall" and bool(state.confidence_decision.get("context_confident", False)):
                final_answer = _memory_recall_recovery_or_alternative()
                draft_answer = final_answer
            elif social_or_non_knowledge and fallback_action == "ANSWER_GENERAL_KNOWLEDGE":
                final_answer = draft_answer
            else:
                final_answer = _clarifier_or_policy_alternative()

    return AnswerAssembleResult(
        draft_answer=draft_answer,
        final_answer=final_answer,
        fallback_action=effective_fallback_action,
        intent_class=intent_class,
        social_or_non_knowledge_intent=social_or_non_knowledge,
        answer_policy_rationale=dict(answer_routing.rationale),
        capability_help_short_circuit=False,
    )


def answer_validate(
    state: PipelineState,
    *,
    assembled: AnswerAssembleResult,
    hits: list[Document],
    chat_history: deque[ChatMsg],
    pending_lookup_override: bool | None,
    build_provenance_metadata,
    evaluate_alignment_decision,
    fallback_answer: str,
    deny_answer: str,
    assist_alternatives_answer: str,
    non_knowledge_uncertainty_answer: str,
    clarify_answer: str,
    route_to_ask_answer: str,
) -> AnswerValidateResult:
    if assembled.intent_class == "time_query" or assembled.fallback_action == "ANSWER_TIME":
        state.confidence_decision["context_confident"] = True

    decision_class = str((assembled.answer_policy_rationale or {}).get("decision_class") or "").strip().lower()
    pending_lookup = (
        bool(pending_lookup_override)
        if pending_lookup_override is not None
        else bool(state.confidence_decision.get("background_ingestion_in_progress", False))
    )
    pending_lookup = pending_lookup or decision_class == DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION.value

    packed_history = pack_chat_history(list(chat_history))
    provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
        final_answer=assembled.final_answer,
        hits=hits,
        chat_history=chat_history,
        packed_history=packed_history,
    )

    if assembled.capability_help_short_circuit:
        _, general_knowledge_contract_applicability, contract_exempt_reason = assess_general_knowledge_contract(
            assembled.final_answer,
            provenance_types=provenance_types,
            confidence_decision=state.confidence_decision,
        )
        alignment_decision = evaluate_alignment_decision(
            user_input=state.user_input,
            draft_answer="",
            final_answer=assembled.final_answer,
            confidence_decision=state.confidence_decision,
            claims=[],
            provenance_types=[],
            basis_statement="No factual claims.",
        )
        alignment_decision["final_alignment_decision"] = "allow"
        return AnswerValidateResult(
            final_answer=assembled.final_answer,
            claims=claims,
            provenance_types=provenance_types,
            used_memory_refs=used_memory_refs,
            used_source_evidence_refs=used_source_evidence_refs,
            source_evidence_attribution=source_evidence_attribution,
            basis_statement=basis_statement,
            invariant_decisions={
                "response_contains_claims": False,
                "has_required_memory_citation": False,
                "answer_contract_valid": True,
                "general_knowledge_contract_valid": True,
                "general_knowledge_contract_applicability": general_knowledge_contract_applicability,
                "contract_exempt_reason": contract_exempt_reason,
                "has_general_knowledge_marker": False,
                "general_knowledge_confidence_gate_passed": True,
                "answer_mode": "assist",
                "fallback_action": "OFFER_CAPABILITY_ALTERNATIVES",
                "provenance_recorded": True,
            },
            alignment_decision=alignment_decision,
        )

    pre_valid, _, _ = assess_general_knowledge_contract(
        assembled.final_answer,
        provenance_types=provenance_types,
        confidence_decision=state.confidence_decision,
    )
    if assembled.final_answer != fallback_answer and not pre_valid and not (
        assembled.intent_class == "time_query"
        or assembled.fallback_action == "ANSWER_TIME"
        or (
            assembled.social_or_non_knowledge_intent
            and bool(assembled.draft_answer)
            and assembled.final_answer == assembled.draft_answer
        )
    ):
        safe_final = non_knowledge_uncertainty_answer
        provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
            final_answer=safe_final,
            hits=hits,
            chat_history=chat_history,
            packed_history=packed_history,
        )
        assembled = replace(assembled, final_answer=safe_final)

    general_valid, general_applicability, contract_exempt_reason = assess_general_knowledge_contract(
        assembled.final_answer,
        provenance_types=provenance_types,
        confidence_decision=state.confidence_decision,
    )
    if assembled.intent_class == "time_query" or assembled.fallback_action == "ANSWER_TIME":
        general_valid = True
        general_applicability = "not_applicable"
        contract_exempt_reason = "time_query"

    alignment_decision = evaluate_alignment_decision(
        user_input=state.user_input,
        draft_answer=assembled.draft_answer,
        final_answer=assembled.final_answer,
        confidence_decision=state.confidence_decision,
        claims=claims,
        provenance_types=provenance_types,
        basis_statement=basis_statement,
    )
    if assembled.intent_class == "time_query" or assembled.fallback_action == "ANSWER_TIME":
        alignment_decision["final_alignment_decision"] = "allow"

    answer_mode_decision = resolve_answer_mode(
        final_answer=assembled.final_answer,
        fallback_action=assembled.fallback_action,
        social_or_non_knowledge_intent=assembled.social_or_non_knowledge_intent,
        is_clarification_answer=is_clarification_answer(
            assembled.final_answer,
            clarify_answer=clarify_answer,
            route_to_ask_answer=route_to_ask_answer,
        ),
        is_deny_answer=assembled.final_answer == deny_answer,
        is_assist_alternatives_answer=assembled.final_answer == assist_alternatives_answer,
        is_fallback_answer=assembled.final_answer == fallback_answer,
        is_non_knowledge_uncertainty_answer=assembled.final_answer == non_knowledge_uncertainty_answer,
        pending_lookup=pending_lookup,
    )
    answer_mode = answer_mode_decision.answer_mode
    ambiguity_policy_allows_non_memory_clarify = bool(state.confidence_decision.get("allow_non_memory_clarify", False))
    explicit_no_clarify_mode = (
        "allow_non_memory_clarify" in state.confidence_decision
        and not ambiguity_policy_allows_non_memory_clarify
    )
    invariant_degrade_reason: str | None = None
    if answer_mode == "clarify" and assembled.intent_class != "memory_recall" and not ambiguity_policy_allows_non_memory_clarify:
        if pending_lookup or explicit_no_clarify_mode:
            safe_final = non_knowledge_uncertainty_answer if pending_lookup else assist_alternatives_answer
            provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
                final_answer=safe_final,
                hits=hits,
                chat_history=chat_history,
                packed_history=packed_history,
            )
            assembled = replace(assembled, final_answer=safe_final)
            answer_mode_decision = resolve_answer_mode(
                final_answer=assembled.final_answer,
                fallback_action=assembled.fallback_action,
                social_or_non_knowledge_intent=assembled.social_or_non_knowledge_intent,
                is_clarification_answer=is_clarification_answer(
                    assembled.final_answer,
                    clarify_answer=clarify_answer,
                    route_to_ask_answer=route_to_ask_answer,
                ),
                is_deny_answer=assembled.final_answer == deny_answer,
                is_assist_alternatives_answer=assembled.final_answer == assist_alternatives_answer,
                is_fallback_answer=assembled.final_answer == fallback_answer,
                is_non_knowledge_uncertainty_answer=assembled.final_answer == non_knowledge_uncertainty_answer,
                pending_lookup=pending_lookup,
            )
            answer_mode = answer_mode_decision.answer_mode
            invariant_degrade_reason = None if pending_lookup else "non_memory_clarify_no_clarify_mode_degraded"
        else:
            raise AssertionError(
                "Non-memory intent produced answer_mode=clarify without explicit ambiguity policy override."
            )

    invariant_decisions = {
        "response_contains_claims": bool(claims),
        "raw_claim_like_text_detected": raw_claim_like_text_detected(assembled.draft_answer),
        "has_required_memory_citation": has_required_memory_citation(assembled.draft_answer),
        "answer_contract_valid": validate_answer_contract(assembled.draft_answer),
        "general_knowledge_contract_valid": general_valid,
        "general_knowledge_contract_applicability": general_applicability,
        "contract_exempt_reason": contract_exempt_reason,
        "has_general_knowledge_marker": has_general_knowledge_marker(assembled.final_answer),
        "general_knowledge_confidence_gate_passed": passes_general_knowledge_confidence_gate(state.confidence_decision),
        "answer_mode": answer_mode,
        "fallback_action": assembled.fallback_action,
        "answer_policy_rationale": assembled.answer_policy_rationale,
        "answer_mode_rationale": answer_mode_decision.rationale,
        "invariant_degrade_reason": invariant_degrade_reason,
        "provenance_recorded": bool(not is_non_trivial_answer(assembled.final_answer) or provenance_types),
    }
    return AnswerValidateResult(
        final_answer=assembled.final_answer,
        claims=claims,
        provenance_types=provenance_types,
        used_memory_refs=used_memory_refs,
        used_source_evidence_refs=used_source_evidence_refs,
        source_evidence_attribution=source_evidence_attribution,
        basis_statement=basis_statement,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )


def answer_routing_from_decision_object(
    decision: DecisionObject,
    *,
    capability_status: CapabilityStatus,
) -> AnswerRoutingDecision:
    warnings.warn(
        "_answer_routing_from_decision_object is deprecated; use _resolve_answer_routing_from_decision_object.",
        DeprecationWarning,
        stacklevel=2,
    )
    return resolve_answer_routing_from_decision_object(decision, capability_status=capability_status)


def resolve_answer_routing_from_decision_object(
    decision: DecisionObject,
    *,
    capability_status: CapabilityStatus,
) -> AnswerRoutingDecision:
    return _resolve_answer_routing_from_decision_object_service(decision, capability_status=capability_status)


def selected_decision_from_confidence(confidence_decision: dict[str, object]) -> DecisionObject | None:
    return _selected_decision_from_confidence_service(confidence_decision)


def resolve_answer_routing_for_stage(
    state: PipelineState,
    *,
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None,
) -> tuple[PipelineState, AnswerRoutingDecision]:
    return _resolve_answer_routing_for_stage_service(
        state,
        capability_status=capability_status,
        selected_decision=selected_decision,
        intent_class_for_policy=intent_class_for_policy,
    )


def decision_object_from_assembled(assembled: AnswerAssembleResult) -> DecisionObject:
    return _decision_object_from_fallback_action(str(assembled.fallback_action or ""))


@dataclass
class AnswerStageFlowDependencies:
    run_canonical_turn_pipeline: object


class _SeededMemoryStore:
    def __init__(self, seeded_hits: list[Document]):
        self._seeded_hits = list(seeded_hits)

    def add_documents(self, documents: list[Document]) -> None:
        self._seeded_hits.extend(documents)

    @staticmethod
    def _normalize(values: set[str] | None) -> set[str]:
        if not values:
            return set()
        return {str(value).strip() for value in values if str(value).strip()}

    @staticmethod
    def _is_excluded(
        doc: Document,
        *,
        exclude_doc_ids: set[str],
        exclude_source_ids: set[str],
        exclude_turn_scoped_ids: set[str],
        segment_ids: set[str],
        segment_types: set[str],
    ) -> bool:
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        doc_id = str(doc.id or metadata.get("doc_id") or "").strip()
        source_doc_id = str(metadata.get("source_doc_id") or "").strip()
        turn_doc_id = str(metadata.get("turn_doc_id") or "").strip()
        if doc_id and doc_id in exclude_doc_ids:
            return True
        if source_doc_id and source_doc_id in exclude_source_ids:
            return True
        if exclude_turn_scoped_ids and any(
            value in exclude_turn_scoped_ids for value in (doc_id, source_doc_id, turn_doc_id) if value
        ):
            return True
        doc_segment_id = str(metadata.get("segment_id") or "").strip()
        doc_segment_type = str(metadata.get("segment_type") or "").strip()
        if segment_ids and doc_segment_id not in segment_ids:
            return True
        if segment_types and doc_segment_type not in segment_types:
            return True
        return bool(
            metadata.get("pipeline_state_snapshot")
            or metadata.get("synthetic_seeded_artifact")
            or metadata.get("seeded_artifact")
        )

    def similarity_search_with_score(self, *_args, **kwargs) -> list[tuple[Document, float]]:
        k = int(kwargs.get("k", 4) or 4)
        exclude_doc_ids = self._normalize(kwargs.get("exclude_doc_ids"))
        exclude_source_ids = self._normalize(kwargs.get("exclude_source_ids"))
        exclude_turn_scoped_ids = self._normalize(kwargs.get("exclude_turn_scoped_ids"))
        segment_ids = self._normalize(kwargs.get("segment_ids"))
        segment_types = self._normalize(kwargs.get("segment_types"))
        filtered = [
            doc
            for doc in self._seeded_hits
            if not self._is_excluded(
                doc,
                exclude_doc_ids=exclude_doc_ids,
                exclude_source_ids=exclude_source_ids,
                exclude_turn_scoped_ids=exclude_turn_scoped_ids,
                segment_ids=segment_ids,
                segment_types=segment_types,
            )
        ]
        return [(doc, 1.0) for doc in filtered[:k]]


def run_canonical_answer_stage_flow(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None,
    runtime_capability_status: RuntimeCapabilityStatus | None,
    clock: Clock | None,
    timezone: str,
    run_canonical_turn_pipeline,
) -> PipelineState:
    if selected_decision is not None:
        warnings.warn(
            "run_canonical_answer_stage_flow(...) ignores selected_decision; canonical policy.decide stage is authoritative.",
            DeprecationWarning,
            stacklevel=2,
        )
    if timezone != "Europe/Helsinki":
        warnings.warn(
            "run_canonical_answer_stage_flow(...) ignores timezone override; canonical turn pipeline clock policy is authoritative.",
            DeprecationWarning,
            stacklevel=2,
        )

    effective_runtime_status = runtime_capability_status or RuntimeCapabilityStatus(
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
    effective_snapshot = CapabilitySnapshot(
        runtime={},
        requested_mode=effective_runtime_status.requested_mode,
        daemon_mode=effective_runtime_status.daemon_mode,
        effective_mode=effective_runtime_status.effective_mode,
        fallback_reason=effective_runtime_status.fallback_reason,
        exit_reason=None,
        ha_error=None,
        ollama_error=None,
        runtime_capability_status=effective_runtime_status,
    )
    seeded_state = replace(
        state,
        classified_intent=state.classified_intent or IntentType.KNOWLEDGE_QUESTION.value,
        resolved_intent=state.resolved_intent or "",
        confidence_decision=dict(state.confidence_decision),
    )
    final_state, _ = run_canonical_turn_pipeline(
        runtime={},
        llm=llm,
        store=_SeededMemoryStore(hits),
        state=seeded_state,
        utterance=seeded_state.user_input,
        prior_pipeline_state=None,
        turn_id=str(uuid.uuid4()),
        near_tie_delta=0.05,
        chat_history=chat_history,
        capability_status=capability_status,
        capability_snapshot=effective_snapshot,
        clock=clock or SystemClock(),
        io_channel="cli",
    )
    return final_state
