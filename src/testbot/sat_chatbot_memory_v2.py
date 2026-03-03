# sat_chatbot_memory_v2.py
from __future__ import annotations

import json
import re
import sys
import uuid
from collections import deque
from pathlib import Path

import arrow
from homeassistant_api import Client

from testbot.config import Config
from testbot.memory_cards import make_reflection_card, make_utterance_card, store_doc, utc_now_iso
from testbot.rerank import adaptive_sigma_fractional, rerank_docs_with_time_and_type
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
            query = llm.invoke(QUERY_REWRITE_PROMPT.format_messages(input=utterance)).content.strip() or utterance
            append_session_log("query_rewrite_output", {"utterance": utterance, "query": query})

            # IMPORTANT: returns List[Tuple[Document, float]]
            docs_and_scores = store.similarity_search_with_score(query, k=12)
            append_session_log(
                "retrieval_candidates",
                {
                    "query": query,
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

            now = arrow.utcnow()
            target = parse_target_time(utterance, now=now)
            sigma = adaptive_sigma_fractional(now=now, target=target, frac=0.25)
            append_session_log(
                "time_target_parse",
                {
                    "utterance": utterance,
                    "now_ts": now.isoformat(),
                    "target_ts": target.isoformat(),
                    "sigma_seconds": sigma,
                },
            )

            hits = rerank_docs_with_time_and_type(
                docs_and_scores,
                now=now,
                target=target,
                sigma_seconds=sigma,
                exclude_doc_ids={u_id, u_ref_id},
                exclude_source_ids={u_id},
                top_k=4,
            )
            context_is_confident = has_sufficient_context_confidence(docs_and_scores)

            # -----------------------
            # 3) Answer using ONLY memory + recent chat
            # -----------------------
            context_str = render_context(hits)
            history_str = format_chat_history(chat_history)

            msgs = ANSWER_PROMPT.format_messages(
                input=utterance,
                chat_history=history_str,
                context=context_str,
            )
            if not context_is_confident:
                reply = "I don't know from memory."
            else:
                draft_reply = (llm.invoke(msgs).content or "").strip()
                if not draft_reply:
                    reply = "I don't know from memory."
                elif validate_answer_contract(draft_reply):
                    reply = draft_reply
                else:
                    reply = "I don't know from memory."
            answer_mode = "dont-know" if reply == "I don't know from memory." else "memory-grounded"
            append_session_log(
                "final_answer_mode",
                {
                    "mode": answer_mode,
                    "query": query,
                    "context_confident": context_is_confident,
                    "retrieved_docs": [
                        (d.id or d.metadata.get("doc_id") or "")
                        for d in hits
                    ],
                },
            )

            sat_say(client, entity_id, reply)

            # -----------------------
            # 4) Store assistant utterance card + reflection card
            # -----------------------
            chat_history.append({"role": "user", "content": utterance})
            chat_history.append({"role": "assistant", "content": reply})

            a_ts = utc_now_iso()
            a_id = str(uuid.uuid4())
            a_card = make_utterance_card(
                ts_iso=a_ts,
                speaker="assistant",
                text=reply,
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
                    "raw": reply,
                },
            )

            a_ref_yaml = generate_reflection_yaml(llm, speaker="assistant", text=reply)
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
