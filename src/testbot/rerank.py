from __future__ import annotations

import math

import arrow
from langchain_core.documents import Document


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
