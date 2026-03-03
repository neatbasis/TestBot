# sat_chatbot_memory_v2.py
from __future__ import annotations

import math
import json
import re
import sys
import uuid
from collections import deque
from pathlib import Path
from typing import Optional

import arrow
from homeassistant_api import Client

from testbot.config import Config
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


# ---------------------------
# Memory cards
# ---------------------------
def utc_now_iso() -> str:
    return arrow.utcnow().isoformat()


def make_utterance_card(*, ts_iso: str, speaker: str, text: str, doc_id: str, channel: str) -> str:
    return (
        f"type: {speaker}_utterance\n"
        f"ts: {ts_iso}\n"
        f"speaker: {speaker}\n"
        f"channel: {channel}\n"
        f"doc_id: {doc_id}\n"
        f"text: {text}\n"
    )


def make_reflection_card(*, ts_iso: str, about: str, source_doc_id: str, doc_id: str, reflection_yaml: str) -> str:
    return (
        "type: reflection\n"
        f"ts: {ts_iso}\n"
        f"about: {about}\n"
        f"source_doc_id: {source_doc_id}\n"
        f"doc_id: {doc_id}\n"
        "reflection:\n"
        f"{reflection_yaml.rstrip()}\n"
    )


def store_doc(store: InMemoryVectorStore, *, doc_id: str, content: str, metadata: dict) -> None:
    """
    Newer LangChain core: attach the id directly on Document.
    """
    doc = Document(id=doc_id, page_content=content, metadata=metadata)
    store.add_documents([doc])


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
# Target time parsing (rule-based)
# ---------------------------
_NUM_SMALL = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_NUM_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_NUM_SPECIAL = {"a": 1, "an": 1, "couple": 2, "few": 3}

_UNIT_ALIASES = {
    "s": "seconds",
    "sec": "seconds",
    "secs": "seconds",
    "second": "seconds",
    "seconds": "seconds",
    "m": "minutes",
    "min": "minutes",
    "mins": "minutes",
    "minute": "minutes",
    "minutes": "minutes",
    "h": "hours",
    "hr": "hours",
    "hrs": "hours",
    "hour": "hours",
    "hours": "hours",
    "d": "days",
    "day": "days",
    "days": "days",
    "w": "weeks",
    "wk": "weeks",
    "wks": "weeks",
    "week": "weeks",
    "weeks": "weeks",
    "mo": "months",
    "month": "months",
    "months": "months",
    "y": "years",
    "yr": "years",
    "yrs": "years",
    "year": "years",
    "years": "years",
}
_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _to_int(num_raw: str) -> Optional[int]:
    s = num_raw.lower().strip()
    if s.isdigit():
        return int(s)
    if s in _NUM_SPECIAL:
        return _NUM_SPECIAL[s]
    if s in _NUM_SMALL:
        return _NUM_SMALL[s]
    if s in _NUM_TENS:
        return _NUM_TENS[s]
    parts = s.split()
    if len(parts) == 2:
        tens, ones = parts
        if tens in _NUM_TENS and ones in _NUM_SMALL:
            return _NUM_TENS[tens] + _NUM_SMALL[ones]
    return None


def _unit_norm(unit_raw: str) -> Optional[str]:
    return _UNIT_ALIASES.get(unit_raw.lower())


_DURATION_RE = re.compile(
    r"\b(?P<num>"
    r"\d+|"
    r"(?:a|an|couple|few|"
    r"zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
    r"(?:\s+(?:one|two|three|four|five|six|seven|eight|nine))?"
    r")"
    r")\s*"
    r"(?P<unit>"
    r"seconds?|secs?|sec|s|"
    r"minutes?|mins?|min|m|"
    r"hours?|hrs?|hr|h|"
    r"days?|d|"
    r"weeks?|wks?|wk|w|"
    r"months?|mo|"
    r"years?|yrs?|yr|y"
    r")\b",
    flags=re.IGNORECASE,
)


def _extract_duration_seconds(text: str) -> Optional[float]:
    m = _DURATION_RE.search(text)
    if not m:
        return None
    n = _to_int(m.group("num"))
    unit = _unit_norm(m.group("unit"))
    if n is None or unit is None:
        return None
    multipliers = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400,
        "weeks": 604800,
        "months": 2629800,  # avg month
        "years": 31557600,  # avg year
    }
    return float(n) * multipliers[unit]


def _weekday_shift(now: arrow.Arrow, target_weekday: int, direction: str) -> arrow.Arrow:
    today = now.weekday()  # Monday=0
    if direction == "next":
        delta = (target_weekday - today) % 7
        delta = 7 if delta == 0 else delta
        return now.shift(days=+delta)
    delta = (today - target_weekday) % 7
    delta = 7 if delta == 0 else delta
    return now.shift(days=-delta)


def parse_target_time(utterance: str, *, now: Optional[arrow.Arrow] = None) -> arrow.Arrow:
    now = now or arrow.utcnow()
    text = utterance.strip().lower()

    if "just now" in text or "right now" in text:
        return now
    if "today" in text:
        return now
    if "yesterday" in text:
        return now.shift(days=-1)
    if "tomorrow" in text:
        return now.shift(days=+1)

    if "last week" in text:
        return now.shift(weeks=-1)
    if "next week" in text:
        return now.shift(weeks=+1)
    if "last month" in text:
        return now.shift(months=-1)
    if "next month" in text:
        return now.shift(months=+1)
    if "last year" in text:
        return now.shift(years=-1)
    if "next year" in text:
        return now.shift(years=+1)

    for wd_name, wd_idx in _WEEKDAY.items():
        if f"next {wd_name}" in text:
            return _weekday_shift(now, wd_idx, "next")
        if f"last {wd_name}" in text:
            return _weekday_shift(now, wd_idx, "last")

    dur_s = _extract_duration_seconds(text)
    if dur_s is not None:
        past_cues = [" ago", " earlier", " before", " previously"]
        future_cues = [" in ", " from now", " later", " after ", " hence"]

        if any(cue in text for cue in past_cues):
            return now.shift(seconds=-int(round(dur_s)))
        if any(cue in text for cue in future_cues):
            return now.shift(seconds=+int(round(dur_s)))

        if "since" in text:
            return now.shift(seconds=-int(round(dur_s)))
        if "until" in text or "till" in text:
            return now.shift(seconds=+int(round(dur_s)))

        return now

    return now


# ---------------------------
# Time-aware reranking (uses similarity scores)
# ---------------------------
def adaptive_sigma_fractional(
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    frac: float = 0.25,          # σ = 25% of |target-now|
    sigma_min: float = 10 * 60,  # 10 min
    sigma_max: float = 30 * 24 * 3600,  # 30 days
) -> float:
    d = abs((target - now).total_seconds())
    sigma = frac * d
    return max(sigma_min, min(sigma, sigma_max))


def time_weight(doc_ts_iso: str, target: arrow.Arrow, sigma_seconds: float) -> float:
    try:
        ts = arrow.get(doc_ts_iso)
        dt = (ts - target).total_seconds()
        return math.exp(-(dt * dt) / (2.0 * sigma_seconds * sigma_seconds))
    except Exception:
        return 0.0


def rerank_docs_with_time_and_type(
    docs_and_scores: list[tuple[Document, float]],
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    sigma_seconds: float,
    exclude_doc_ids: set[str],
    exclude_source_ids: set[str],
    top_k: int = 4,
) -> list[Document]:
    """
    docs_and_scores: output of similarity_search_with_score -> [(doc, sim_score), ...]
    """
    scored: list[tuple[float, Document]] = []

    for doc, sim in docs_and_scores:
        doc_id = (doc.id or doc.metadata.get("doc_id") or "").strip()
        if doc_id and doc_id in exclude_doc_ids:
            continue
        if doc.metadata.get("source_doc_id") in exclude_source_ids:
            continue

        t = doc.metadata.get("type", "")
        type_prior = 0.7 if t == "reflection" else 1.0

        tw = time_weight(doc.metadata.get("ts", ""), target, sigma_seconds)

        # combine: similarity * time * type
        # keep some similarity even if time weight is weak
        score = type_prior * float(sim) * (0.25 + 0.75 * tw)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]


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
            "When you use memory, cite doc_id and ts.\n\n"
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
            reply = (llm.invoke(msgs).content or "").strip() or "I don't know from memory."
            answer_mode = "dont-know" if reply == "I don't know from memory." else "memory-grounded"
            append_session_log(
                "final_answer_mode",
                {
                    "mode": answer_mode,
                    "query": query,
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
