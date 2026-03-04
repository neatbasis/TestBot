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

from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType, append_pipeline_snapshot
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action
from testbot.rerank import adaptive_sigma_fractional, rerank_docs_with_time_and_type_outcome
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
from ha_ask import AskSpec, ask_question
from ha_ask.config import normalize_rest_api_url

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
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
ALIGNMENT_OBJECTIVE_VERSION = "2026-03-01.v1"
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
    return {
        "ha_api_url": os.getenv("HA_API_URL", "http://localhost:8123"),
        "ha_api_secret": os.getenv("HA_API_SECRET", ""),
        "ha_satellite_entity_id": os.getenv("HA_SATELLITE_ENTITY_ID", ""),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434",
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
        "memory_near_tie_delta": float(os.getenv("MEMORY_NEAR_TIE_DELTA", "0.02")),
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


def _print_startup_status(*, selected_mode: str, daemon_mode: bool, runtime: dict[str, object], ha_error: str | None) -> None:
    print("=== TestBot startup status ===")
    print(f"Selected mode: {selected_mode} (daemon={daemon_mode})")
    print(f"Ollama endpoint: {runtime['ollama_base_url']} model={runtime['ollama_model']}")
    if ha_error:
        print(f"Home Assistant: unavailable ({ha_error})")
        print(f"Install warning [YELLOW]: Home Assistant capability is degraded; configure HA_API_SECRET and HA_SATELLITE_ENTITY_ID to enable satellite mode.")
        print("Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set.")
    else:
        print(f"Home Assistant: available ({runtime['ha_api_url']}, entity={runtime['ha_satellite_entity_id']})")
        print("Install warning [GREEN]: Home Assistant capability is active; keep Home Assistant credentials configured when reinstalling or reprovisioning.")
        print("Developer note: satellite ask/speak loop is enabled.")
    print("Continuity: memory cards are shared across interfaces in-process via one vector store.")
    print("==============================")


def format_chat_history(hist: deque[ChatMsg]) -> str:
    lines: list[str] = []
    for m in hist:
        role = m.get("role", "unknown")
        content = (m.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


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


def stage_retrieve(store: InMemoryVectorStore, state: PipelineState) -> tuple[PipelineState, list[tuple[Document, float]]]:
    docs_and_scores = store.similarity_search_with_score(state.rewritten_query, k=12)
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
) -> tuple[PipelineState, list[Document]]:
    now = arrow.utcnow()
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
    return "non_memory"


def stage_answer(
    llm: ChatOllama,
    state: PipelineState,
    *,
    chat_history: deque[ChatMsg],
    hits: list[Document],
    capability_status: CapabilityStatus,
) -> PipelineState:
    context_str = render_context(hits)
    history_str = format_chat_history(chat_history)
    msgs = ANSWER_PROMPT.format_messages(input=state.user_input, chat_history=history_str, context=context_str)

    fallback_action = decide_fallback_action(
        intent=_intent_class_for_policy(state.user_input),
        memory_hit=bool(state.confidence_decision.get("context_confident", False)),
        ambiguity=bool(state.confidence_decision.get("ambiguity_detected", False)),
        capability_status=capability_status,
    )

    if is_unsafe_user_request(state.user_input):
        draft_answer = ""
        final_answer = DENY_ANSWER
    elif fallback_action == "ROUTE_TO_ASK":
        draft_answer = ""
        final_answer = ROUTE_TO_ASK_ANSWER
    elif fallback_action == "ASK_CLARIFYING_QUESTION":
        draft_answer = ""
        final_answer = CLARIFY_ANSWER
    elif fallback_action == "EXACT_MEMORY_FALLBACK":
        draft_answer = ""
        final_answer = FALLBACK_ANSWER
    else:
        draft_answer = (llm.invoke(msgs).content or "").strip()
        if not draft_answer:
            final_answer = FALLBACK_ANSWER
        elif validate_answer_contract(draft_answer):
            final_answer = draft_answer
        else:
            final_answer = FALLBACK_ANSWER

    alignment_decision = evaluate_alignment_decision(
        user_input=state.user_input,
        draft_answer=draft_answer,
        final_answer=final_answer,
        confidence_decision=state.confidence_decision,
    )

    provenance_types, claims, basis_statement, used_memory_refs = build_provenance_metadata(
        final_answer=final_answer,
        hits=hits,
        chat_history=chat_history,
    )

    invariant_decisions = {
        "response_contains_claims": response_contains_claims(draft_answer),
        "has_required_memory_citation": has_required_memory_citation(draft_answer),
        "answer_contract_valid": validate_answer_contract(draft_answer),
        "answer_mode": (
            "deny"
            if final_answer == DENY_ANSWER
            else (
                "dont-know"
                if final_answer == FALLBACK_ANSWER
                else (
                    "clarify"
                    if final_answer in {CLARIFY_ANSWER, ROUTE_TO_ASK_ANSWER}
                    else "memory-grounded"
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
            "If the memory does not contain the answer, say: \"I don't know from memory.\"\n"
            "For any factual claim, include at least one cited memory with both doc_id and ts.\n"
            "If confidence in memory context is low or context is insufficient, respond EXACTLY: \"I don't know from memory.\"\n\n"
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
    }


def extract_claims(text: str) -> list[str]:
    if not is_non_trivial_answer(text):
        return []
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return parts[:4]


def collect_used_memory_refs(hits: list[Document]) -> list[str]:
    refs: list[str] = []
    for d in hits:
        doc_id = str(d.id or d.metadata.get("doc_id") or "").strip()
        if not doc_id:
            continue
        ts = str(d.metadata.get("ts") or "").strip()
        refs.append(f"{doc_id}@{ts}" if ts else doc_id)
    return list(dict.fromkeys(refs))


def build_provenance_metadata(
    *,
    final_answer: str,
    hits: list[Document],
    chat_history: deque[ChatMsg],
) -> tuple[list[ProvenanceType], list[str], str, list[str]]:
    if not is_non_trivial_answer(final_answer):
        return (
            [ProvenanceType.UNKNOWN],
            [],
            "Trivial fallback/deny/clarification response with no substantive claim.",
            [],
        )

    used_memory_refs = collect_used_memory_refs(hits)
    claims = extract_claims(final_answer)
    provenance_types: list[ProvenanceType] = [ProvenanceType.INFERENCE]
    if used_memory_refs:
        provenance_types.append(ProvenanceType.MEMORY)
    if chat_history:
        provenance_types.append(ProvenanceType.CHAT_HISTORY)

    basis_statement = (
        "Answer synthesized from reranked memory context"
        + (" and recent chat history." if chat_history else ".")
    )
    return list(dict.fromkeys(provenance_types)), claims, basis_statement, used_memory_refs

def response_contains_claims(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    if normalized == "I don't know from memory.":
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


def is_unsafe_user_request(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(re.search(r"\b(bypass|exploit|weapon|harm|poison|malware)\b", lowered))


def evaluate_alignment_decision(
    *,
    user_input: str,
    draft_answer: str,
    final_answer: str,
    confidence_decision: dict[str, object],
) -> dict[str, object]:
    has_claims = response_contains_claims(draft_answer)
    has_citation = has_required_memory_citation(draft_answer)
    context_confident = bool(confidence_decision.get("context_confident", False))
    unsafe_request = is_unsafe_user_request(user_input)

    factual_grounding_reliability = 1.0 if (not has_claims or (has_citation and context_confident)) else 0.0
    safety_compliance_strictness = 0.0 if (unsafe_request and final_answer != DENY_ANSWER) else 1.0
    response_utility = 1.0 if final_answer not in {"", FALLBACK_ANSWER, DENY_ANSWER} else 0.4
    cost_latency_budget = 1.0

    if safety_compliance_strictness < 1.0:
        final_alignment_decision = "deny"
    elif factual_grounding_reliability < 1.0:
        final_alignment_decision = "fallback"
    elif response_utility < 0.5:
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
        },
        "final_alignment_decision": final_alignment_decision,
    }


def _run_chat_loop(
    *,
    llm: ChatOllama,
    store: InMemoryVectorStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: CapabilityStatus,
    read_user_utterance,
    send_assistant_text,
) -> None:
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

        state = PipelineState(user_input=utterance)
        append_pipeline_snapshot("ingest", state)

        _validate_and_log_transition(validate_observe_pre(state))
        state = observe_stage(state)
        _validate_and_log_transition(validate_observe_post(state))
        append_pipeline_snapshot("observe", state)

            # -----------------------
            # 1) Store user utterance card + reflection card
            # -----------------------
        now_iso = utc_now_iso()
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
        u_ref_ts = utc_now_iso()
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
        )
        _validate_and_log_transition(validate_rerank_post(state))
        append_pipeline_snapshot("rerank", state)
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
                "basis_statement": state.basis_statement,
            },
        )

        send_assistant_text(state.final_answer)

            # -----------------------
            # 4) Store assistant utterance card + reflection card
            # -----------------------
        chat_history.append({"role": "user", "content": utterance})
        chat_history.append({"role": "assistant", "content": state.final_answer})

        a_ts = utc_now_iso()
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
        a_ref_ts = utc_now_iso()
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


def _run_cli_mode(*, llm: ChatOllama, store: InMemoryVectorStore, chat_history: deque[ChatMsg], near_tie_delta: float) -> None:
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
    )


def _run_satellite_mode(
    *,
    llm: ChatOllama,
    store: InMemoryVectorStore,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    api_url: str,
    token: str,
    entity_id: str,
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
        )


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    runtime = _read_runtime_env()

    llm = ChatOllama(model=str(runtime["ollama_model"]), base_url=str(runtime["ollama_base_url"]), temperature=0.0)
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=str(runtime["ollama_base_url"]))
    store = InMemoryVectorStore(embeddings)
    chat_history: deque[ChatMsg] = deque(maxlen=10)

    ha_error = _ha_connection_error(
        str(runtime["ha_api_url"]),
        str(runtime["ha_api_secret"]),
        str(runtime["ha_satellite_entity_id"]),
    )

    selected_mode = _resolve_mode(args.mode, ha_error)

    _print_startup_status(selected_mode=selected_mode, daemon_mode=args.daemon, runtime=runtime, ha_error=ha_error)

    if selected_mode == "satellite":
        if ha_error is not None:
            if args.daemon:
                print(f"Daemon mode requested and Home Assistant is unavailable: {ha_error}", file=sys.stderr)
                return
            print("Falling back to CLI mode because satellite connection is unavailable.")
            selected_mode = "cli"
        else:
            _run_satellite_mode(
                llm=llm,
                store=store,
                chat_history=chat_history,
                near_tie_delta=float(runtime["memory_near_tie_delta"]),
                api_url=str(runtime["ha_api_url"]),
                token=str(runtime["ha_api_secret"]),
                entity_id=str(runtime["ha_satellite_entity_id"]),
            )
            return

    _run_cli_mode(
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=float(runtime["memory_near_tie_delta"]),
    )

    return


if __name__ == "__main__":
    main()
