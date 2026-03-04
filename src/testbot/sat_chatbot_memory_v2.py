# sat_chatbot_memory_v2.py
from __future__ import annotations

import json
import re
import sys
import uuid
from collections import deque
from dataclasses import replace
from pathlib import Path

import arrow
from homeassistant_api import Client

from testbot.config import Config
from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.pipeline_state import CandidateHit, PipelineState, append_pipeline_snapshot
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


def stage_answer(llm: ChatOllama, state: PipelineState, *, chat_history: deque[ChatMsg], hits: list[Document]) -> PipelineState:
    context_str = render_context(hits)
    history_str = format_chat_history(chat_history)
    msgs = ANSWER_PROMPT.format_messages(input=state.user_input, chat_history=history_str, context=context_str)

    if not state.confidence_decision.get("context_confident", False):
        draft_answer = ""
        final_answer = "I don't know from memory."
    else:
        draft_answer = (llm.invoke(msgs).content or "").strip()
        if not draft_answer:
            final_answer = "I don't know from memory."
        elif validate_answer_contract(draft_answer):
            final_answer = draft_answer
        else:
            final_answer = "I don't know from memory."

    invariant_decisions = {
        "response_contains_claims": response_contains_claims(draft_answer),
        "has_required_memory_citation": has_required_memory_citation(draft_answer),
        "answer_contract_valid": validate_answer_contract(draft_answer),
        "answer_mode": "dont-know" if final_answer == "I don't know from memory." else "memory-grounded",
    }
    return replace(state, draft_answer=draft_answer, final_answer=final_answer, invariant_decisions=invariant_decisions)


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


def main() -> None:
    cfg = Config.from_env()

    api_url = cfg.HA_API_URL
    token = cfg.HA_API_SECRET
    entity_id = cfg.HA_SATELLITE_ENTITY_ID

    if not api_url or not token:
        print("Missing HA_API_URL or HA_API_SECRET in .env", file=sys.stderr)
        return
    if not entity_id:
        print("Missing HA_SATELLITE_ENTITY_ID in .env", file=sys.stderr)
        return

    ollama_host = cfg.OLLAMA_BASE_URL
    ollama_model = cfg.OLLAMA_MODEL

    llm = ChatOllama(model=ollama_model, base_url=ollama_host, temperature=0.0)
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_host)

    # Newer langchain-core InMemoryVectorStore: pass embeddings directly
    store = InMemoryVectorStore(embeddings)

    chat_history: deque[ChatMsg] = deque(maxlen=10)

    rest = normalize_rest_api_url(api_url)

    with Client(rest, token) as client:
        sat_say(
            client,
            entity_id,
            "v0 memory loop online. Ask one memory-based question. Say 'stop' to exit.",
        )

        while True:
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
                continue

            utterance = (res.get("sentence") or "").strip()
            if not utterance:
                sat_say(client, entity_id, "I heard silence. Try again.")
                continue

            append_session_log(
                "user_utterance_ingest",
                {
                    "channel": "satellite",
                    "utterance": utterance,
                },
            )

            low = utterance.lower()
            if low in {"stop", "quit", "exit"}:
                sat_say(client, entity_id, "Stopping. Bye.")
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
                channel="satellite",
            )
            store_doc(
                store,
                doc_id=u_id,
                content=u_card,
                metadata={
                    "ts": now_iso,
                    "type": "user_utterance",
                    "speaker": "user",
                    "channel": "satellite",
                    "doc_id": u_id,          # keep for convenience
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

            # IMPORTANT: returns List[Tuple[Document, float]]
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
                near_tie_delta=cfg.MEMORY_NEAR_TIE_DELTA,
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
            state = stage_answer(llm, state, chat_history=chat_history, hits=hits)
            _validate_and_log_transition(validate_answer_post(state))
            append_pipeline_snapshot("answer", state)
            append_session_log(
                "final_answer_mode",
                {
                    "mode": state.invariant_decisions.get("answer_mode", "dont-know"),
                    "query": state.rewritten_query,
                    "context_confident": state.confidence_decision.get("context_confident", False),
                    "retrieved_docs": [
                        (d.id or d.metadata.get("doc_id") or "")
                        for d in hits
                    ],
                },
            )

            sat_say(client, entity_id, state.final_answer)

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
                channel="satellite",
            )
            store_doc(
                store,
                doc_id=a_id,
                content=a_card,
                metadata={
                    "ts": a_ts,
                    "type": "assistant_utterance",
                    "speaker": "assistant",
                    "channel": "satellite",
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

    return


if __name__ == "__main__":
    main()
