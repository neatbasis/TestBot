# sat_chatbot_memory_v2.py
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from argparse import ArgumentParser, Namespace
from collections import deque
from dataclasses import replace
from pathlib import Path

import arrow
from homeassistant_api import Client

from testbot.clock import Clock, SystemClock
from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType, append_pipeline_snapshot
from testbot.promotion_policy import persist_promoted_context
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action
from testbot.rerank import (
    adaptive_sigma_fractional,
    is_source_evidence_doc,
    mix_source_evidence_with_memory_cards,
    rerank_docs_with_time_and_type_outcome,
)
from testbot.stage_transitions import (
    append_transition_validation_log,
    validate_answer_post,
    validate_answer_pre,
    validate_encode_post,
    validate_encode_pre,
    validate_observe_post,
    validate_observe_pre,
    validate_rerank_post,
    validate_rerank_pre,
    validate_retrieve_post,
    validate_retrieve_pre,
)
from testbot.time_parse import parse_target_time
from testbot.intent_router import IntentType, classify_intent
from testbot.time_reasoning import elapsed_since_last_user_message, resolve_relative_date
from ha_ask import AskSpec, ask_question
from ha_ask.config import normalize_rest_api_url
from testbot.history_packer import PackedHistory, labeled_history_claims, pack_chat_history, render_packed_history

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from testbot.vector_store import MemoryStore, build_memory_store, normalize_memory_store_mode
from langchain_ollama import ChatOllama, OllamaEmbeddings


# ---------------------------
# HA satellite output
# ---------------------------
def sat_say(client: Client, entity_id: str, text: str) -> None:
    client.trigger_service(
        "assist_satellite",
        "start_conversation",
        entity_id=entity_id,
        start_message=text,
        preannounce=False,
    )


# ---------------------------
# Chat history (short-term memory)
# ---------------------------
ChatMsg = dict[str, str]

FALLBACK_ANSWER = "I don't know from memory."
DENY_ANSWER = "I can't comply with that request."
CLARIFY_ANSWER = "Can you clarify which memory and time window you mean?"
ROUTE_TO_ASK_ANSWER = "I can disambiguate this with a quick follow-up question."
ASSIST_ALTERNATIVES_ANSWER = (
    "I don't have enough reliable memory to answer directly. "
    "I can either help you reconstruct the timeline from what you remember, "
    "or suggest where to check next for the missing detail."
)
CAPABILITIES_HELP_ANSWER = (
    "I can help with: memory-grounded recall; general explanation support; clarifying-question support when "
    "memory is incomplete; Home Assistant actions (with a degraded message when unavailable); and debug visibility "
    "only when debug mode is enabled."
)
GENERAL_KNOWLEDGE_MARKER_PREFIX = "General definition (not from your memory):"
GENERAL_KNOWLEDGE_CONFIDENCE_MIN = 0.85
GENERAL_KNOWLEDGE_SUPPORT_MIN = 2
ALIGNMENT_OBJECTIVE_VERSION = "2026-03-04.v2"
SESSION_LOG_SCHEMA_VERSION = 2


def _parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(description="Run TestBot with satellite or CLI chat interfaces.")
    parser.add_argument(
        "--mode",
        choices=("auto", "satellite", "cli"),
        default="auto",
        help="Input/output mode. auto prefers satellite and falls back to CLI.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Do not fall back to CLI if satellite mode is unavailable; exit instead.",
    )
    return parser.parse_args(argv)


def _read_runtime_env() -> dict[str, object]:
    memory_store_mode = os.getenv("MEMORY_STORE_MODE", "in_memory")
    return {
        "ha_api_url": os.getenv("HA_API_URL", "http://localhost:8123"),
        "ha_api_secret": os.getenv("HA_API_SECRET", ""),
        "ha_satellite_entity_id": os.getenv("HA_SATELLITE_ENTITY_ID", ""),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434",
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
        "memory_near_tie_delta": float(os.getenv("MEMORY_NEAR_TIE_DELTA", "0.02")),
        "memory_store_mode": memory_store_mode,
        "memory_store_backend": normalize_memory_store_mode(memory_store_mode),
        "elasticsearch_url": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        "elasticsearch_index": os.getenv("ELASTICSEARCH_INDEX", "testbot_memory_cards"),
    }


def _ha_connection_error(api_url: str, token: str, entity_id: str) -> str | None:
    if not token:
        return "Missing HA_API_SECRET"
    if not entity_id:
        return "Missing HA_SATELLITE_ENTITY_ID"
    try:
        with Client(normalize_rest_api_url(api_url), token):
            return None
    except Exception as exc:  # pragma: no cover - network/credential dependent
        return f"{type(exc).__name__}: {exc}"


def _resolve_mode(requested_mode: str, ha_error: str | None) -> str:
    if requested_mode == "auto":
        return "satellite" if ha_error is None else "cli"
    return requested_mode


def _resolve_effective_mode(
    *,
    requested_mode: str,
    daemon_mode: bool,
    ha_error: str | None,
) -> tuple[str | None, str | None, str | None]:
    if requested_mode == "auto" and ha_error is not None and daemon_mode:
        return None, None, f"Home Assistant is unavailable: {ha_error}"

    selected_mode = _resolve_mode(requested_mode, ha_error)
    if selected_mode == "satellite" and ha_error is not None:
        if daemon_mode:
            return None, None, f"Home Assistant is unavailable: {ha_error}"
        return "cli", "satellite connection is unavailable", None
    return selected_mode, None, None


def _print_startup_status(
    *,
    requested_mode: str,
    effective_mode: str,
    daemon_mode: bool,
    runtime: dict[str, object],
    ha_error: str | None,
    fallback_reason: str | None = None,
) -> None:
    print("=== TestBot startup status ===")
    if fallback_reason:
        print(f"Selected mode: {effective_mode} (requested={requested_mode}, fallback reason={fallback_reason}, daemon={daemon_mode})")
    else:
        print(f"Selected mode: {effective_mode} (requested={requested_mode}, daemon={daemon_mode})")
    print(f"Ollama endpoint: {runtime['ollama_base_url']} model={runtime['ollama_model']}")
    print(f"Memory backend: {runtime['memory_store_backend']}")
    if ha_error:
        print(f"Home Assistant: unavailable ({ha_error})")
        print("Install warning [YELLOW]: Home Assistant capability is degraded; configure HA_API_SECRET and HA_SATELLITE_ENTITY_ID to enable satellite mode.")
        print("Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set.")
    else:
        print(f"Home Assistant: available ({runtime['ha_api_url']}, entity={runtime['ha_satellite_entity_id']})")
        print("Install warning [GREEN]: Home Assistant capability is active; keep Home Assistant credentials configured when reinstalling or reprovisioning.")
        print("Developer note: satellite ask/speak loop is enabled.")
    print("Continuity: memory cards are shared across interfaces in-process via one vector store.")
    print("==============================")


def append_session_log(event: str, payload: dict, *, log_path: Path = Path("./logs/session.jsonl")) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": event,
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        **payload,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def doc_to_candidate_hit(doc: Document, score: float) -> CandidateHit:
    return CandidateHit(
        doc_id=str(doc.id or doc.metadata.get("doc_id") or ""),
        score=float(score),
        ts=str(doc.metadata.get("ts") or ""),
        card_type=str(doc.metadata.get("type") or ""),
    )


def stage_rewrite_query(llm: ChatOllama, state: PipelineState) -> PipelineState:
    rewritten_query = llm.invoke(QUERY_REWRITE_PROMPT.format_messages(input=state.user_input)).content.strip() or state.user_input
    return replace(state, rewritten_query=rewritten_query)


def observe_stage(state: PipelineState) -> PipelineState:
    return state


def encode_stage(llm: ChatOllama, state: PipelineState) -> PipelineState:
    return stage_rewrite_query(llm, state)


def stage_retrieve(store: MemoryStore, state: PipelineState) -> tuple[PipelineState, list[tuple[Document, float]]]:
    raw_docs_and_scores = store.similarity_search_with_score(state.rewritten_query, k=18)
    docs_and_scores = mix_source_evidence_with_memory_cards(raw_docs_and_scores, top_k=12, source_quota=3)
    retrieval_candidates = [doc_to_candidate_hit(doc, score) for doc, score in docs_and_scores]
    return replace(state, retrieval_candidates=retrieval_candidates), docs_and_scores


def stage_rerank(
    state: PipelineState,
    docs_and_scores: list[tuple[Document, float]],
    *,
    utterance: str,
    user_doc_id: str,
    user_reflection_doc_id: str,
    near_tie_delta: float,
    clock: Clock,
) -> tuple[PipelineState, list[Document]]:
    now = clock.now()
    target = parse_target_time(utterance, now=now)
    sigma = adaptive_sigma_fractional(now=now, target=target, frac=0.25)
    rerank_outcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=target,
        sigma_seconds=sigma,
        exclude_doc_ids={user_doc_id, user_reflection_doc_id},
        exclude_source_ids={user_doc_id},
        top_k=4,
        near_tie_delta=near_tie_delta,
    )
    hits = rerank_outcome.docs
    reranked_hits = [doc_to_candidate_hit(doc, score=0.0) for doc in hits]
    has_context = has_sufficient_context_confidence(docs_and_scores)
    confidence_decision = {
        "context_confident": has_context and not rerank_outcome.ambiguity_detected,
        "ambiguity_detected": rerank_outcome.ambiguity_detected,
        "ambiguous_candidates": rerank_outcome.near_tie_candidates,
        "scored_candidates": rerank_outcome.scored_candidates,
        "now_ts": now.isoformat(),
        "target_ts": target.isoformat(),
        "sigma_seconds": sigma,
    }
    return replace(state, reranked_hits=reranked_hits, confidence_decision=confidence_decision), hits


def _intent_class_for_policy(user_input: str) -> str:
    intent = classify_intent(user_input)
    if intent == IntentType.MEMORY_RECALL:
        return "memory_recall"
    if intent == IntentType.TIME_QUERY:
        return "time_query"
    return "non_memory"


def _is_capabilities_help_request(user_input: str) -> bool:
    return classify_intent(user_input) == IntentType.CAPABILITIES_HELP


def _intent_label(intent: IntentType) -> str:
    return intent.value


def _ambiguity_score(confidence_decision: dict[str, object]) -> float:
    scored_candidates = confidence_decision.get("scored_candidates", [])
    if not isinstance(scored_candidates, list) or len(scored_candidates) < 2:
        return 0.0
    first = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
    second = scored_candidates[1] if isinstance(scored_candidates[1], dict) else {}
    first_score = float(first.get("final_score", 0.0) or 0.0)
    second_score = float(second.get("final_score", 0.0) or 0.0)
    if first_score <= 0.0:
        return 1.0
    separation = max(0.0, first_score - second_score) / first_score
    return round(max(0.0, min(1.0, 1.0 - separation)), 4)


def _user_followup_signal_proxy(*, final_answer: str, fallback_action: str, ambiguity_score: float) -> float:
    if final_answer in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER}:
        return 1.0
    if fallback_action in {"ASK_CLARIFYING_QUESTION", "ROUTE_TO_ASK"}:
        return 0.9
    if fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        return round(max(0.2, ambiguity_score), 4)
    return round(max(0.0, ambiguity_score * 0.5), 4)


def build_partial_memory_clarifier(hits: list[Document], *, max_items: int = 2) -> str:
    snippets: list[str] = []
    for doc in hits[:max_items]:
        snippet = (doc.page_content or "").strip()
        if snippet:
            snippets.append(snippet[:80])
    if snippets:
        joined = "; ".join(snippets)
        return (
            f"I found related memory fragments ({joined}), but not enough to answer precisely. "
            "Which person, event, or time window should I focus on?"
        )
    return CLARIFY_ANSWER


def is_clarification_answer(text: str) -> bool:
    normalized = (text or "").strip()
    return normalized in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER} or normalized.startswith(
        "I found related memory fragments ("
    )


def _build_time_answer(*, user_input: str, now: arrow.Arrow, last_user_message_ts: str | None, timezone: str) -> str:
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


def stage_answer(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
    clock: Clock,
    timezone: str = "Europe/Helsinki",
) -> PipelineState:
    if _is_capabilities_help_request(state.user_input):
        final_answer = CAPABILITIES_HELP_ANSWER
        provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
            final_answer=final_answer,
            hits=hits,
            chat_history=chat_history,
            packed_history=pack_chat_history(list(chat_history)),
        )
        alignment_decision = evaluate_alignment_decision(
            user_input=state.user_input,
            draft_answer="",
            final_answer=final_answer,
            confidence_decision=state.confidence_decision,
            claims=claims,
            provenance_types=provenance_types,
            basis_statement=basis_statement,
        )
        return replace(
            state,
            draft_answer="",
            final_answer=final_answer,
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
                "has_general_knowledge_marker": False,
                "general_knowledge_confidence_gate_passed": True,
                "answer_mode": "assist",
                "fallback_action": "ANSWER_GENERAL_KNOWLEDGE",
                "provenance_recorded": True,
            },
            alignment_decision=alignment_decision,
        )

    context_str = render_context(hits)
    packed_history = pack_chat_history(list(chat_history))
    history_str = render_packed_history(packed_history)
    msgs = ANSWER_PROMPT.format_messages(input=state.user_input, chat_history=history_str, context=context_str)

    fallback_action = decide_fallback_action(
        intent=_intent_class_for_policy(state.user_input),
        memory_hit=bool(state.confidence_decision.get("context_confident", False)),
        ambiguity=bool(state.confidence_decision.get("ambiguity_detected", False)),
        capability_status=capability_status,
        source_confidence=(
            float(state.confidence_decision["source_confidence"])
            if "source_confidence" in state.confidence_decision
            else None
        ),
    )

    if is_unsafe_user_request(state.user_input):
        draft_answer = ""
        final_answer = DENY_ANSWER
    elif fallback_action == "ROUTE_TO_ASK":
        draft_answer = ""
        final_answer = ROUTE_TO_ASK_ANSWER
    elif fallback_action == "ASK_CLARIFYING_QUESTION":
        draft_answer = ""
        final_answer = build_partial_memory_clarifier(hits)
    elif fallback_action == "ANSWER_UNKNOWN":
        draft_answer = FALLBACK_ANSWER
        final_answer = FALLBACK_ANSWER
    elif fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        draft_answer = ""
        final_answer = ASSIST_ALTERNATIVES_ANSWER
    elif fallback_action == "ANSWER_TIME":
        draft_answer = ""
        final_answer = _build_time_answer(
            user_input=state.user_input,
            now=clock.now(),
            last_user_message_ts=state.last_user_message_ts,
            timezone=timezone,
        )
    else:
        draft_answer = (llm.invoke(msgs).content or "").strip()
        if not draft_answer:
            final_answer = ASSIST_ALTERNATIVES_ANSWER
        elif validate_answer_contract(draft_answer):
            final_answer = draft_answer
        else:
            final_answer = build_partial_memory_clarifier(hits)

    provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
        final_answer=final_answer,
        hits=hits,
        chat_history=chat_history,
        packed_history=packed_history,
    )

    general_knowledge_contract_valid = (
        True
        if fallback_action == "ANSWER_TIME"
        else validate_general_knowledge_contract(
            final_answer,
            provenance_types=provenance_types,
            confidence_decision=state.confidence_decision,
        )
    )
    if final_answer != FALLBACK_ANSWER and not general_knowledge_contract_valid:
        final_answer = build_partial_memory_clarifier(hits)
        provenance_types, claims, basis_statement, used_memory_refs, used_source_evidence_refs, source_evidence_attribution = build_provenance_metadata(
            final_answer=final_answer,
            hits=hits,
            chat_history=chat_history,
            packed_history=packed_history,
        )

    alignment_decision = evaluate_alignment_decision(
        user_input=state.user_input,
        draft_answer=draft_answer,
        final_answer=final_answer,
        confidence_decision=state.confidence_decision,
        claims=claims,
        provenance_types=provenance_types,
        basis_statement=basis_statement,
    )

    invariant_decisions = {
        "response_contains_claims": response_contains_claims(draft_answer),
        "has_required_memory_citation": has_required_memory_citation(draft_answer),
        "answer_contract_valid": validate_answer_contract(draft_answer),
        "general_knowledge_contract_valid": general_knowledge_contract_valid,
        "has_general_knowledge_marker": has_general_knowledge_marker(final_answer),
        "general_knowledge_confidence_gate_passed": passes_general_knowledge_confidence_gate(state.confidence_decision),
        "answer_mode": (
            "deny"
            if final_answer == DENY_ANSWER
            else (
                "clarify"
                if is_clarification_answer(final_answer)
                else (
                    "assist"
                    if final_answer == ASSIST_ALTERNATIVES_ANSWER
                    else ("dont-know" if final_answer == FALLBACK_ANSWER else "memory-grounded")
                )
            )
        ),
        "fallback_action": fallback_action,
        "provenance_recorded": bool(not is_non_trivial_answer(final_answer) or provenance_types),
    }
    return replace(
        state,
        draft_answer=draft_answer,
        final_answer=final_answer,
        claims=claims,
        provenance_types=provenance_types,
        used_memory_refs=used_memory_refs,
        used_source_evidence_refs=used_source_evidence_refs,
        source_evidence_attribution=source_evidence_attribution,
        basis_statement=basis_statement,
        invariant_decisions=invariant_decisions,
        alignment_decision=alignment_decision,
    )


def _validate_and_log_transition(result) -> None:
    append_transition_validation_log(result)
    if not result.passed:
        failures = ", ".join(result.failures)
        raise AssertionError(f"Stage transition validation failed at {result.stage}.{result.boundary}: {failures}")


# ---------------------------
# Reflection extraction (metacognition)
# ---------------------------
REFLECTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a metacognitive reflection extractor.\n"
            "Given an observed statement, produce compact YAML with ONLY these keys:\n"
            "claims: [..]\n"
            "commitments: [..]\n"
            "preferences: [..]\n"
            "uncertainties: [..]\n"
            "followups: [..]\n"
            "confidence: <0..1>\n"
            "Rules:\n"
            "- Keep each list item short.\n"
            "- If none, use empty list [].\n"
            "- Do NOT invent facts.\n"
            "- If uncertain, put it under uncertainties.\n"
            "- Output YAML only (no prose).\n",
        ),
        ("human", "speaker: {speaker}\ntext: {text}\n"),
    ]
)


def generate_reflection_yaml(llm: ChatOllama, *, speaker: str, text: str) -> str:
    msgs = REFLECTION_PROMPT.format_messages(speaker=speaker, text=text)
    out = llm.invoke(msgs).content
    return (out or "").strip() or (
        "claims: []\ncommitments: []\npreferences: []\nuncertainties: []\nfollowups: []\nconfidence: 0.2"
    )


# ---------------------------
# RAG prompt (uses chat history + retrieved memory)
# ---------------------------
ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful assistant.\n"
            "Use ONLY the provided memory context and recent chat.\n"
            "If memory is empty or low-confidence, ask one targeted clarifying question or offer at least two capability-based alternatives.\n"
            "If memory is partial or ambiguous, provide a short user-facing summary and one bridging clarifier.\n"
            "Keep the exact phrase \"I don't know from memory.\" only for explicit deny/safety-policy cases.\n"
            "For any factual claim, include at least one cited memory with both doc_id and ts.\n\n"
            "Recent chat:\n{chat_history}\n\n"
            "Memory context:\n{context}\n",
        ),
        ("human", "{input}"),
    ]
)

QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "Rewrite the user's message into a short search query for retrieving relevant memory.\nReturn ONLY the query text."),
        ("human", "{input}"),
    ]
)


def render_context(docs: list[Document], *, limit_chars: int = 5000) -> str:
    chunks: list[str] = []
    total = 0
    for d in docs:
        s = (d.page_content or "").strip()
        if not s:
            continue
        add = s + "\n---\n"
        if total + len(add) > limit_chars:
            break
        chunks.append(add)
        total += len(add)
    return "".join(chunks).strip()


def has_sufficient_context_confidence(
    docs_and_scores: list[tuple[Document, float]], *, min_similarity: float = 0.35, min_hits: int = 1
) -> bool:
    if len(docs_and_scores) < min_hits:
        return False
    return max(float(score) for _, score in docs_and_scores) >= min_similarity




def is_non_trivial_answer(text: str) -> bool:
    normalized = (text or "").strip()
    return bool(normalized) and normalized not in {
        FALLBACK_ANSWER,
        DENY_ANSWER,
        CLARIFY_ANSWER,
        ROUTE_TO_ASK_ANSWER,
        ASSIST_ALTERNATIVES_ANSWER,
    }


def extract_claims(text: str) -> list[str]:
    if not is_non_trivial_answer(text):
        return []
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return parts[:4]


def collect_used_memory_refs(hits: list[Document]) -> list[str]:
    refs: list[str] = []
    for d in hits:
        if is_source_evidence_doc(d):
            continue
        doc_id = str(d.id or d.metadata.get("doc_id") or "").strip()
        if not doc_id:
            continue
        ts = str(d.metadata.get("ts") or "").strip()
        refs.append(f"{doc_id}@{ts}" if ts else doc_id)
    return list(dict.fromkeys(refs))


def collect_used_source_evidence_refs(hits: list[Document]) -> tuple[list[str], list[dict[str, str]]]:
    refs: list[str] = []
    attributions: list[dict[str, str]] = []
    for d in hits:
        if not is_source_evidence_doc(d):
            continue
        doc_id = str(d.id or d.metadata.get("doc_id") or "").strip()
        if doc_id:
            refs.append(doc_id)
        attribution = {
            "doc_id": doc_id,
            "source_type": str(d.metadata.get("source_type") or ""),
            "source_uri": str(d.metadata.get("source_uri") or ""),
            "retrieved_at": str(d.metadata.get("retrieved_at") or ""),
            "trust_tier": str(d.metadata.get("trust_tier") or ""),
        }
        attributions.append(attribution)
    deduped_refs = list(dict.fromkeys(refs))
    deduped_attributions = list({json.dumps(item, sort_keys=True): item for item in attributions}.values())
    return deduped_refs, deduped_attributions


def build_provenance_metadata(
    *,
    final_answer: str,
    hits: list[Document],
    chat_history: deque[ChatMsg],
    packed_history: PackedHistory,
) -> tuple[list[ProvenanceType], list[str], str, list[str], list[str], list[dict[str, str]]]:
    if not is_non_trivial_answer(final_answer):
        return (
            [ProvenanceType.UNKNOWN],
            [],
            "Trivial fallback/deny/clarification response with no substantive claim.",
            [],
            [],
            [],
        )

    used_memory_refs = collect_used_memory_refs(hits)
    used_source_evidence_refs, source_evidence_attribution = collect_used_source_evidence_refs(hits)
    claims = [f"INFERENCE: {claim}" for claim in extract_claims(final_answer)]
    claims.extend(labeled_history_claims(packed_history))
    claims = claims[:8]
    provenance_types: list[ProvenanceType] = [ProvenanceType.INFERENCE]
    if used_memory_refs or used_source_evidence_refs:
        provenance_types.append(ProvenanceType.MEMORY)
    else:
        provenance_types.append(ProvenanceType.GENERAL_KNOWLEDGE)
    if chat_history:
        provenance_types.append(ProvenanceType.CHAT_HISTORY)

    if used_memory_refs:
        basis_statement = (
            "Answer synthesized from reranked memory context"
            + (" and recent chat history." if chat_history else ".")
        )
    elif used_source_evidence_refs:
        basis_statement = "Answer synthesized from reranked source evidence documents."
    elif chat_history:
        basis_statement = (
            "Relevance summary basis: synthesized from recent chat history signals."
            if final_answer.startswith("Relevant summary:")
            else "Answer synthesized from recent chat history."
        )
    else:
        basis_statement = "General-knowledge basis: no supporting memory references were retrieved."
    return (
        list(dict.fromkeys(provenance_types)),
        claims,
        basis_statement,
        used_memory_refs,
        used_source_evidence_refs,
        source_evidence_attribution,
    )

def response_contains_claims(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if normalized in {FALLBACK_ANSWER, CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER, ASSIST_ALTERNATIVES_ANSWER}:
        return False
    # A simple heuristic: if there is sentence-like prose, treat it as factual/semantic claims.
    return bool(re.search(r"[A-Za-z0-9].{8,}", normalized))


def has_required_memory_citation(text: str) -> bool:
    citation_pattern = re.compile(r"doc_id\s*[:=]\s*[^,\]\)\n]+.*?ts\s*[:=]\s*[^,\]\)\n]+", re.IGNORECASE)
    return bool(citation_pattern.search(text or ""))


def validate_answer_contract(text: str) -> bool:
    if not response_contains_claims(text):
        return True
    return has_required_memory_citation(text)


def has_general_knowledge_marker(text: str) -> bool:
    normalized = (text or "").strip().lower()
    return normalized.startswith(GENERAL_KNOWLEDGE_MARKER_PREFIX.lower())


def passes_general_knowledge_confidence_gate(confidence_decision: dict[str, object]) -> bool:
    confidence = float(confidence_decision.get("general_knowledge_confidence", 0.0) or 0.0)
    support_count = int(confidence_decision.get("general_knowledge_support", 0) or 0)
    return confidence >= GENERAL_KNOWLEDGE_CONFIDENCE_MIN and support_count >= GENERAL_KNOWLEDGE_SUPPORT_MIN


def validate_general_knowledge_contract(
    text: str,
    *,
    provenance_types: list[ProvenanceType],
    confidence_decision: dict[str, object],
) -> bool:
    if not response_contains_claims(text):
        return True
    if ProvenanceType.GENERAL_KNOWLEDGE not in provenance_types:
        return True
    return has_general_knowledge_marker(text) and passes_general_knowledge_confidence_gate(confidence_decision)


def is_unsafe_user_request(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(re.search(r"\b(bypass|exploit|weapon|harm|poison|malware)\b", lowered))


def evaluate_alignment_decision(
    *,
    user_input: str,
    draft_answer: str,
    final_answer: str,
    confidence_decision: dict[str, object],
    claims: list[str],
    provenance_types: list[ProvenanceType],
    basis_statement: str,
) -> dict[str, object]:
    contract_exempt_response = is_clarification_answer(final_answer) or final_answer in {
        ASSIST_ALTERNATIVES_ANSWER,
        CAPABILITIES_HELP_ANSWER,
    }
    has_claims = response_contains_claims(draft_answer)
    has_citation = has_required_memory_citation(draft_answer)
    context_confident = bool(confidence_decision.get("context_confident", False))
    unsafe_request = is_unsafe_user_request(user_input)

    factual_grounding_reliability = 1.0 if (
        contract_exempt_response or not has_claims or (has_citation and context_confident)
    ) else 0.0
    safety_compliance_strictness = 0.0 if (unsafe_request and final_answer != DENY_ANSWER) else 1.0
    response_utility = 1.0 if final_answer not in {"", FALLBACK_ANSWER, DENY_ANSWER} else 0.4
    cost_latency_budget = 1.0
    provenance_transparency = 1.0 if (
        not is_non_trivial_answer(final_answer)
        or (bool(claims) and bool(provenance_types) and bool((basis_statement or "").strip()))
    ) else 0.0

    if safety_compliance_strictness < 1.0:
        final_alignment_decision = "deny"
    elif factual_grounding_reliability < 1.0:
        final_alignment_decision = "fallback"
    elif response_utility < 0.5:
        final_alignment_decision = "fallback"
    elif provenance_transparency < 1.0:
        final_alignment_decision = "fallback"
    else:
        final_alignment_decision = "allow"

    return {
        "objective_version": ALIGNMENT_OBJECTIVE_VERSION,
        "dimensions": {
            "factual_grounding_reliability": factual_grounding_reliability,
            "safety_compliance_strictness": safety_compliance_strictness,
            "response_utility": response_utility,
            "cost_latency_budget": cost_latency_budget,
            "provenance_transparency": provenance_transparency,
        },
        "final_alignment_decision": final_alignment_decision,
    }


def _run_chat_loop(
    *,
    llm: ChatOllama,
    store: MemoryStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: CapabilityStatus,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
) -> None:
    last_user_message_ts = ""
    while True:
        utterance = read_user_utterance()
        if utterance is None:
            return
        utterance = utterance.strip()
        if not utterance:
            send_assistant_text("I heard silence. Try again.")
            continue

        append_session_log(
            "user_utterance_ingest",
            {
                "channel": io_channel,
                "utterance": utterance,
            },
        )

        low = utterance.lower()
        if low in {"stop", "quit", "exit"}:
            send_assistant_text("Stopping. Bye.")
            break

        state = PipelineState(user_input=utterance, last_user_message_ts=last_user_message_ts)
        append_pipeline_snapshot("ingest", state)

        _validate_and_log_transition(validate_observe_pre(state))
        state = observe_stage(state)
        _validate_and_log_transition(validate_observe_post(state))
        append_pipeline_snapshot("observe", state)

            # -----------------------
            # 1) Store user utterance card + reflection card
            # -----------------------
        now_iso = clock.now().isoformat()
        u_id = str(uuid.uuid4())

        u_card = make_utterance_card(
            ts_iso=now_iso,
            speaker="user",
            text=utterance,
            doc_id=u_id,
            channel=io_channel,
        )
        store_doc(
            store,
            doc_id=u_id,
            content=u_card,
            metadata={
                "ts": now_iso,
                "type": "user_utterance",
                "speaker": "user",
                "channel": io_channel,
                "doc_id": u_id,
                "raw": utterance,
            },
        )

        u_ref_yaml = generate_reflection_yaml(llm, speaker="user", text=utterance)
        u_ref_ts = clock.now().isoformat()
        u_ref_id = str(uuid.uuid4())

        u_ref_card = make_reflection_card(
            ts_iso=u_ref_ts,
            about="user",
            source_doc_id=u_id,
            doc_id=u_ref_id,
            reflection_yaml=u_ref_yaml,
        )
        store_doc(
            store,
            doc_id=u_ref_id,
            content=u_ref_card,
            metadata={
                "ts": u_ref_ts,
                "type": "reflection",
                "about": "user",
                "source_doc_id": u_id,
                "doc_id": u_ref_id,
            },
        )

            # -----------------------
            # 2) Retrieve + time-aware rerank (FIXED: handle tuples)
            # -----------------------
        _validate_and_log_transition(validate_encode_pre(state))
        state = encode_stage(llm, state)
        _validate_and_log_transition(validate_encode_post(state))
        append_pipeline_snapshot("rewrite", state)
        append_session_log("query_rewrite_output", {"utterance": utterance, "query": state.rewritten_query})

        _validate_and_log_transition(validate_retrieve_pre(state))
        state, docs_and_scores = stage_retrieve(store, state)
        _validate_and_log_transition(validate_retrieve_post(state))
        append_pipeline_snapshot("retrieve", state)
        append_session_log(
            "retrieval_candidates",
            {
                "query": state.rewritten_query,
                "candidate_count": len(docs_and_scores),
                "top_candidates": [
                    {
                        "doc_id": (doc.id or doc.metadata.get("doc_id") or ""),
                        "score": float(score),
                    }
                    for doc, score in docs_and_scores[:4]
                ],
            },
        )

        _validate_and_log_transition(validate_rerank_pre(state))
        state, hits = stage_rerank(
            state,
            docs_and_scores,
            utterance=utterance,
            user_doc_id=u_id,
            user_reflection_doc_id=u_ref_id,
            near_tie_delta=near_tie_delta,
            clock=clock,
        )
        _validate_and_log_transition(validate_rerank_post(state))
        append_pipeline_snapshot("rerank", state)
        classified_intent = classify_intent(utterance)
        intent_label = _intent_label(classified_intent)
        ambiguity_score = _ambiguity_score(state.confidence_decision)
        append_session_log(
            "intent_classified",
            {
                "utterance": utterance,
                "intent": intent_label,
                "ambiguity_score": ambiguity_score,
                "user_followup_signal_proxy": round(ambiguity_score, 4),
            },
        )
        append_session_log(
            "time_target_parse",
            {
                "utterance": utterance,
                "now_ts": state.confidence_decision.get("now_ts", ""),
                "target_ts": state.confidence_decision.get("target_ts", ""),
                "sigma_seconds": state.confidence_decision.get("sigma_seconds", 0.0),
                "objective_candidates": state.confidence_decision.get("scored_candidates", []),
            },
        )
        if state.confidence_decision.get("ambiguity_detected", False):
            append_session_log(
                "ambiguity_detected",
                {
                    "query": state.rewritten_query,
                    "candidates": state.confidence_decision.get("ambiguous_candidates", []),
                },
            )

            # -----------------------
            # 3) Answer using ONLY memory + recent chat
            # -----------------------
        _validate_and_log_transition(validate_answer_pre(state))
        state = stage_answer(
            llm,
            state,
            chat_history=chat_history,
            hits=hits,
            capability_status=capability_status,
            clock=clock,
        )
        _validate_and_log_transition(validate_answer_post(state))
        append_pipeline_snapshot("answer", state)
        append_session_log(
            "final_answer_mode",
            {
                "mode": state.invariant_decisions.get("answer_mode", "dont-know"),
                "query": state.rewritten_query,
                "context_confident": state.confidence_decision.get("context_confident", False),
                "retrieved_docs": [(d.id or d.metadata.get("doc_id") or "") for d in hits],
                "claims": state.claims,
                "provenance_types": [p.value for p in state.provenance_types],
                "used_memory_refs": state.used_memory_refs,
                "used_source_evidence_refs": state.used_source_evidence_refs,
                "source_evidence_attribution": state.source_evidence_attribution,
                "basis_statement": state.basis_statement,
            },
        )
        chosen_action = str(state.invariant_decisions.get("fallback_action", "NONE"))
        followup_proxy = _user_followup_signal_proxy(
            final_answer=state.final_answer,
            fallback_action=chosen_action,
            ambiguity_score=ambiguity_score,
        )
        append_session_log(
            "fallback_action_selected",
            {
                "utterance": utterance,
                "intent": intent_label,
                "ambiguity_score": ambiguity_score,
                "chosen_action": chosen_action,
                "user_followup_signal_proxy": followup_proxy,
            },
        )
        append_session_log(
            "provenance_summary",
            {
                "utterance": utterance,
                "intent": intent_label,
                "ambiguity_score": ambiguity_score,
                "chosen_action": chosen_action,
                "user_followup_signal_proxy": followup_proxy,
                "claims": state.claims,
                "provenance_types": [p.value for p in state.provenance_types],
                "used_memory_refs": state.used_memory_refs,
                "used_source_evidence_refs": state.used_source_evidence_refs,
                "source_evidence_attribution": state.source_evidence_attribution,
                "basis_statement": state.basis_statement,
            },
        )

        send_assistant_text(state.final_answer)

            # -----------------------
            # 4) Store assistant utterance card + reflection card
            # -----------------------
        last_user_message_ts = now_iso
        chat_history.append({"role": "user", "content": utterance})
        chat_history.append({"role": "assistant", "content": state.final_answer})

        a_ts = clock.now().isoformat()
        a_id = str(uuid.uuid4())
        a_card = make_utterance_card(
            ts_iso=a_ts,
            speaker="assistant",
            text=state.final_answer,
            doc_id=a_id,
            channel=io_channel,
        )
        store_doc(
            store,
            doc_id=a_id,
            content=a_card,
            metadata={
                "ts": a_ts,
                "type": "assistant_utterance",
                "speaker": "assistant",
                "channel": io_channel,
                "doc_id": a_id,
                "raw": state.final_answer,
            },
        )

        a_ref_yaml = generate_reflection_yaml(llm, speaker="assistant", text=state.final_answer)
        a_ref_ts = clock.now().isoformat()
        a_ref_id = str(uuid.uuid4())
        a_ref_card = make_reflection_card(
            ts_iso=a_ref_ts,
            about="assistant",
            source_doc_id=a_id,
            doc_id=a_ref_id,
            reflection_yaml=a_ref_yaml,
        )
        store_doc(
            store,
            doc_id=a_ref_id,
            content=a_ref_card,
            metadata={
                "ts": a_ref_ts,
                "type": "reflection",
                "about": "assistant",
                "source_doc_id": a_id,
                "doc_id": a_ref_id,
            },
        )

        promoted_doc_ids = persist_promoted_context(
            store=store,
            ts_iso=a_ref_ts,
            source_doc_id=a_id,
            source_reflection_id=a_ref_id,
            reflection_yaml=a_ref_yaml,
            channel=io_channel,
        )
        if promoted_doc_ids:
            append_session_log(
                "promoted_context_persisted",
                {
                    "source_doc_id": a_id,
                    "source_reflection_id": a_ref_id,
                    "promoted_doc_ids": promoted_doc_ids,
                    "count": len(promoted_doc_ids),
                },
            )


def _run_cli_mode(*, llm: ChatOllama, store: MemoryStore, chat_history: deque[ChatMsg], near_tie_delta: float, clock: Clock) -> None:
    print("CLI chat ready. Ask memory-grounded questions; type 'stop' to exit.")

    def _read() -> str | None:
        try:
            return input("you> ")
        except EOFError:
            return None

    def _send(text: str) -> None:
        print(f"bot> {text}")

    _run_chat_loop(
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel="cli",
        capability_status="ask_unavailable",
        read_user_utterance=_read,
        send_assistant_text=_send,
        clock=clock,
    )


def _run_satellite_mode(
    *,
    llm: ChatOllama,
    store: MemoryStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    api_url: str,
    token: str,
    entity_id: str,
    clock: Clock,
) -> None:
    rest = normalize_rest_api_url(api_url)
    with Client(rest, token) as client:
        sat_say(client, entity_id, "v0 memory loop online. Ask one memory-based question. Say 'stop' to exit.")

        def _read() -> str | None:
            res = ask_question(
                channel="satellite",
                spec=AskSpec(
                    question="Ask one memory-grounded question.",
                    answers=None,
                    timeout_s=60.0,
                ),
                api_url=api_url,
                token=token,
                satellite_entity_id=entity_id,
            )
            if res.get("error"):
                sat_say(client, entity_id, f"I didn't get that. Error: {res['error']}")
                return ""
            return str(res.get("sentence") or "")

        def _send(text: str) -> None:
            sat_say(client, entity_id, text)

        _run_chat_loop(
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=near_tie_delta,
            io_channel="satellite",
            capability_status="ask_available",
            read_user_utterance=_read,
            send_assistant_text=_send,
            clock=clock,
        )


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    runtime = _read_runtime_env()

    llm = ChatOllama(model=str(runtime["ollama_model"]), base_url=str(runtime["ollama_base_url"]), temperature=0.0)
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=str(runtime["ollama_base_url"]))
    store = build_memory_store(
        embeddings=embeddings,
        mode=str(runtime["memory_store_mode"]),
        elasticsearch_url=str(runtime["elasticsearch_url"]),
        elasticsearch_index=str(runtime["elasticsearch_index"]),
    )
    chat_history: deque[ChatMsg] = deque(maxlen=10)
    clock = SystemClock()

    ha_error = _ha_connection_error(
        str(runtime["ha_api_url"]),
        str(runtime["ha_api_secret"]),
        str(runtime["ha_satellite_entity_id"]),
    )

    effective_mode, fallback_reason, exit_reason = _resolve_effective_mode(
        requested_mode=args.mode,
        daemon_mode=args.daemon,
        ha_error=ha_error,
    )

    append_session_log(
        "startup_mode_resolution",
        {
            "requested_mode": args.mode,
            "effective_mode": effective_mode,
            "daemon_mode": args.daemon,
            "ha_available": ha_error is None,
            "ha_error": ha_error,
            "fallback_reason": fallback_reason,
            "exit_reason": exit_reason,
        },
    )

    if effective_mode is None:
        if args.mode == "auto":
            print(f"Daemon mode requested in auto mode and {exit_reason}", file=sys.stderr)
        else:
            print(f"Daemon mode requested and {exit_reason}", file=sys.stderr)
        return

    _print_startup_status(
        requested_mode=args.mode,
        effective_mode=effective_mode,
        daemon_mode=args.daemon,
        runtime=runtime,
        ha_error=ha_error,
        fallback_reason=fallback_reason,
    )

    if effective_mode == "satellite":
        _run_satellite_mode(
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=float(runtime["memory_near_tie_delta"]),
            api_url=str(runtime["ha_api_url"]),
            token=str(runtime["ha_api_secret"]),
            entity_id=str(runtime["ha_satellite_entity_id"]),
            clock=clock,
        )
        return

    _run_cli_mode(
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=float(runtime["memory_near_tie_delta"]),
        clock=clock,
    )

    return


if __name__ == "__main__":
    main()
