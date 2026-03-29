"""Canonical answer-stage presentation collaborators.

This module owns answer-stage prompt/render inputs used by the runtime turn
pipeline when assembling user-facing answers.
"""

from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful assistant.\n"
            "Use ONLY the provided memory context and recent chat.\nHeuristic packed-history hints are advisory context only, never hard evidence.\n"
            "If memory is empty or low-confidence, ask one targeted clarifying question or offer at least two capability-based alternatives.\n"
            "If memory is partial or ambiguous, provide a short user-facing summary and one bridging clarifier.\n"
            "Keep the exact phrase \"I don't know from memory.\" only for explicit deny/safety-policy cases.\n"
            "For any factual claim, include at least one cited memory with both doc_id and ts.\n\n"
            "Recent chat:\n{chat_history}\n\n"
            "Memory context:\n{context}\n\n"
            "Deterministic response plan:\n{response_plan}\n",
        ),
        ("human", "{input}"),
    ]
)


def render_context(docs: list[Document], *, limit_chars: int = 5000) -> str:
    chunks: list[str] = []
    total = 0
    for idx, d in enumerate(docs, start=1):
        snippet = re.sub(r"\s+", " ", (d.page_content or "").strip())
        if not snippet:
            continue
        doc_id = str(d.metadata.get("doc_id") or d.id or "")
        ts = str(d.metadata.get("ts") or "")
        doc_type = str(d.metadata.get("type") or "")
        block = (
            f"[doc_{idx}]\n"
            f"doc_id: {doc_id}\n"
            f"ts: {ts}\n"
            f"type: {doc_type}\n"
            f"content: {snippet}\n"
            "---\n"
        )
        if total + len(block) > limit_chars:
            break
        chunks.append(block)
        total += len(block)
    return "".join(chunks).strip()
