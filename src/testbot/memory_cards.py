from __future__ import annotations

from dataclasses import dataclass

import arrow
from langchain_core.documents import Document
from testbot.ports import PortDocument
from testbot.vector_store import MemoryStore


@dataclass(frozen=True)
class UtteranceCard:
    ts_iso: str
    speaker: str
    text: str
    doc_id: str
    channel: str


@dataclass(frozen=True)
class ReflectionCard:
    ts_iso: str
    about: str
    source_doc_id: str
    doc_id: str
    reflection_yaml: str


def utc_now_iso() -> str:
    return arrow.utcnow().isoformat()


def make_utterance_card(*, ts_iso: str, speaker: str, text: str, doc_id: str, channel: str) -> str:
    card = UtteranceCard(ts_iso=ts_iso, speaker=speaker, text=text, doc_id=doc_id, channel=channel)
    return (
        f"type: {card.speaker}_utterance\n"
        f"ts: {card.ts_iso}\n"
        f"speaker: {card.speaker}\n"
        f"channel: {card.channel}\n"
        f"doc_id: {card.doc_id}\n"
        f"text: {card.text}\n"
    )


def make_reflection_card(*, ts_iso: str, about: str, source_doc_id: str, doc_id: str, reflection_yaml: str) -> str:
    card = ReflectionCard(
        ts_iso=ts_iso,
        about=about,
        source_doc_id=source_doc_id,
        doc_id=doc_id,
        reflection_yaml=reflection_yaml,
    )
    return (
        "type: reflection\n"
        f"ts: {card.ts_iso}\n"
        f"about: {card.about}\n"
        f"source_doc_id: {card.source_doc_id}\n"
        f"doc_id: {card.doc_id}\n"
        "reflection:\n"
        f"{card.reflection_yaml.rstrip()}\n"
    )


def store_doc(store: MemoryStore, *, doc_id: str, content: str, metadata: dict) -> None:
    doc = PortDocument(doc_id=doc_id, content=content, metadata=metadata)
    if hasattr(store, "add_memory_records"):
        store.add_memory_records([doc])
        return
    legacy_doc = Document(id=doc_id, page_content=content, metadata=metadata)
    store.add_documents([legacy_doc])
