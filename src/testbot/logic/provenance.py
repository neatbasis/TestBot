from __future__ import annotations

import json
from collections import deque

from langchain_core.documents import Document

from testbot.history_packer import PackedHistory, labeled_history_claims
from testbot.logic.alignment import extract_claims, is_non_trivial_answer
from testbot.pipeline_state import ProvenanceType
from testbot.rerank import is_source_evidence_doc

ChatMsg = dict[str, str]


def collect_used_memory_refs(hits: list[Document]) -> list[str]:
    refs: list[str] = []
    for doc in hits:
        if is_source_evidence_doc(doc):
            continue
        doc_id = str(doc.metadata.get("doc_id") or doc.id or "").strip()
        if not doc_id:
            continue
        ts = str(doc.metadata.get("ts") or "").strip()
        refs.append(f"{doc_id}@{ts}" if ts else doc_id)
    return sorted(dict.fromkeys(refs))


def collect_used_source_evidence_refs(hits: list[Document]) -> tuple[list[str], list[dict[str, str]]]:
    refs: list[str] = []
    attributions: list[dict[str, str]] = []
    for doc in hits:
        if not is_source_evidence_doc(doc):
            continue
        doc_id = str(doc.metadata.get("doc_id") or doc.id or "").strip()
        if doc_id:
            refs.append(doc_id)
        attribution = {
            "doc_id": doc_id,
            "source_type": str(doc.metadata.get("source_type") or ""),
            "source_uri": str(doc.metadata.get("source_uri") or ""),
            "retrieved_at": str(doc.metadata.get("retrieved_at") or ""),
            "trust_tier": str(doc.metadata.get("trust_tier") or ""),
        }
        attributions.append(attribution)
    deduped_refs = sorted(dict.fromkeys(refs))
    deduped_attributions = list({json.dumps(item, sort_keys=True): item for item in attributions}.values())
    deduped_attributions.sort(key=lambda item: (item.get("doc_id", ""), item.get("source_uri", ""), item.get("retrieved_at", "")))
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

    if used_memory_refs and used_source_evidence_refs:
        basis_statement = (
            "Answer synthesized from reranked memory context and source evidence documents"
            + (" with recent chat history signals." if chat_history else ".")
        )
    elif used_memory_refs:
        basis_statement = (
            "Answer synthesized from reranked memory context"
            + (" and recent chat history." if chat_history else ".")
        )
    elif used_source_evidence_refs:
        basis_statement = (
            "Answer synthesized from reranked source evidence documents"
            + (" and recent chat history." if chat_history else ".")
        )
    elif chat_history:
        basis_statement = (
            "Relevance summary basis: synthesized from recent chat history signals."
            if final_answer.startswith("Relevant summary:")
            else "Answer synthesized from recent chat history (advisory signals only)."
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


__all__ = [
    "build_provenance_metadata",
    "collect_used_memory_refs",
    "collect_used_source_evidence_refs",
]
