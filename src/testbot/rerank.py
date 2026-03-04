from __future__ import annotations

import math
from dataclasses import dataclass

import arrow
from langchain_core.documents import Document


@dataclass(frozen=True)
class RerankOutcome:
    docs: list[Document]
    ambiguity_detected: bool
    near_tie_candidates: list[dict[str, float | str]]


_CARD_TYPE_PRIORITY: dict[str, int] = {
    "user_utterance": 0,
    "assistant_utterance": 1,
    "memory": 2,
    "reflection": 3,
}


def adaptive_sigma_fractional(
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    frac: float = 0.25,  # σ = 25% of |target-now|
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


def similarity_with_time_and_type_score(
    *,
    sim_score: float,
    doc_type: str,
    doc_ts_iso: str,
    target: arrow.Arrow,
    sigma_seconds: float,
) -> float:
    type_prior = 0.7 if doc_type == "reflection" else 1.0
    tw = time_weight(doc_ts_iso, target, sigma_seconds)

    # combine: similarity * time * type
    # keep some similarity even if time weight is weak
    return type_prior * float(sim_score) * (0.25 + 0.75 * tw)


def _doc_id(doc: Document) -> str:
    return str(doc.id or doc.metadata.get("doc_id") or "").strip()


def _ts_epoch(doc: Document) -> float:
    raw = str(doc.metadata.get("ts") or "").strip()
    if not raw:
        return float("-inf")
    try:
        return arrow.get(raw).float_timestamp
    except Exception:
        return float("-inf")


def _card_rank(doc: Document) -> int:
    doc_type = str(doc.metadata.get("type") or "")
    return _CARD_TYPE_PRIORITY.get(doc_type, 2)


def _tie_break_key(doc: Document) -> tuple[float, int, str]:
    # Newer timestamp first; non-reflection cards first; doc_id lexical for stable ordering.
    return (_ts_epoch(doc), -_card_rank(doc), _doc_id(doc))


def rerank_docs_with_time_and_type(
    docs_and_scores: list[tuple[Document, float]],
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    sigma_seconds: float,
    exclude_doc_ids: set[str],
    exclude_source_ids: set[str],
    top_k: int = 4,
    near_tie_delta: float = 0.02,
) -> list[Document]:
    return rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now,
        target=target,
        sigma_seconds=sigma_seconds,
        exclude_doc_ids=exclude_doc_ids,
        exclude_source_ids=exclude_source_ids,
        top_k=top_k,
        near_tie_delta=near_tie_delta,
    ).docs


def rerank_docs_with_time_and_type_outcome(
    docs_and_scores: list[tuple[Document, float]],
    *,
    now: arrow.Arrow,
    target: arrow.Arrow,
    sigma_seconds: float,
    exclude_doc_ids: set[str],
    exclude_source_ids: set[str],
    top_k: int = 4,
    near_tie_delta: float = 0.02,
) -> RerankOutcome:
    """
    docs_and_scores: output of similarity_search_with_score -> [(doc, sim_score), ...]
    """
    del now  # kept for call-site signature parity.

    scored: list[tuple[float, Document]] = []

    for doc, sim in docs_and_scores:
        doc_id = _doc_id(doc)
        if doc_id and doc_id in exclude_doc_ids:
            continue
        if doc.metadata.get("source_doc_id") in exclude_source_ids:
            continue

        score = similarity_with_time_and_type_score(
            sim_score=sim,
            doc_type=doc.metadata.get("type", ""),
            doc_ts_iso=doc.metadata.get("ts", ""),
            target=target,
            sigma_seconds=sigma_seconds,
        )
        scored.append((score, doc))

    scored.sort(key=lambda x: (-x[0], -_ts_epoch(x[1]), _card_rank(x[1]), _doc_id(x[1])))
    docs = [d for _, d in scored[:top_k]]

    near_tie_candidates: list[dict[str, float | str]] = []
    ambiguity_detected = False
    if scored:
        top_score = scored[0][0]
        near_tie = [(score, doc) for score, doc in scored if (top_score - score) <= near_tie_delta]
        near_tie_candidates = [
            {
                "doc_id": _doc_id(doc),
                "score": float(score),
            }
            for score, doc in near_tie
        ]

        if len(near_tie) > 1:
            top_key = _tie_break_key(near_tie[0][1])
            unresolved = [doc for _, doc in near_tie if _tie_break_key(doc) == top_key]
            ambiguity_detected = len(unresolved) > 1

    return RerankOutcome(docs=docs, ambiguity_detected=ambiguity_detected, near_tie_candidates=near_tie_candidates)
