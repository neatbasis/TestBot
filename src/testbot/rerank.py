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
    scored_candidates: list[dict[str, float | str]]


RERANK_OBJECTIVE_NAME = "semantic_temporal_type_v1"


@dataclass(frozen=True)
class RerankObjectiveCoefficients:
    base_temporal_blend: float = 0.25
    gaussian_temporal_blend: float = 0.75
    reflection_type_prior: float = 0.7
    default_type_prior: float = 1.0


DEFAULT_RERANK_COEFFICIENTS = RerankObjectiveCoefficients()


_CARD_TYPE_PRIORITY: dict[str, int] = {
    "user_utterance": 0,
    "assistant_utterance": 1,
    "memory": 2,
    "source_evidence": 3,
    "reflection": 4,
}




def is_source_evidence_doc(doc: Document) -> bool:
    doc_type = str(doc.metadata.get("type") or "").strip()
    record_kind = str(doc.metadata.get("record_kind") or "").strip()
    return doc_type == "source_evidence" or record_kind == "source_evidence"


def mix_source_evidence_with_memory_cards(
    docs_and_scores: list[tuple[Document, float]],
    *,
    top_k: int,
    source_quota: int = 2,
) -> list[tuple[Document, float]]:
    """Mix source evidence with memory cards while keeping deterministic fallback behavior."""
    if not docs_and_scores:
        return []

    source_candidates: list[tuple[Document, float]] = []
    memory_candidates: list[tuple[Document, float]] = []
    for doc, score in docs_and_scores:
        if is_source_evidence_doc(doc):
            source_candidates.append((doc, score))
        else:
            memory_candidates.append((doc, score))

    if not source_candidates:
        return docs_and_scores[:top_k]

    ordered_source = sorted(source_candidates, key=lambda item: (-item[1], -_ts_epoch(item[0]), _card_rank(item[0]), _doc_id(item[0])))
    ordered_memory = sorted(memory_candidates, key=lambda item: (-item[1], -_ts_epoch(item[0]), _card_rank(item[0]), _doc_id(item[0])))

    mixed: list[tuple[Document, float]] = []
    source_taken = min(source_quota, top_k)
    mixed.extend(ordered_source[:source_taken])

    remaining = top_k - len(mixed)
    if remaining > 0:
        mixed.extend(ordered_memory[:remaining])

    remaining = top_k - len(mixed)
    if remaining > 0:
        mixed.extend(ordered_source[source_taken : source_taken + remaining])

    return mixed


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
    return rerank_objective_score_components(
        sim_score=sim_score,
        doc_type=doc_type,
        doc_ts_iso=doc_ts_iso,
        target=target,
        sigma_seconds=sigma_seconds,
    )["final_score"]


def rerank_objective_score_components(
    *,
    sim_score: float,
    doc_type: str,
    doc_ts_iso: str,
    target: arrow.Arrow,
    sigma_seconds: float,
    coefficients: RerankObjectiveCoefficients = DEFAULT_RERANK_COEFFICIENTS,
) -> dict[str, float | str]:
    temporal_gaussian_weight = time_weight(doc_ts_iso, target, sigma_seconds)
    type_prior = coefficients.reflection_type_prior if doc_type == "reflection" else coefficients.default_type_prior
    temporal_blend = coefficients.base_temporal_blend + (coefficients.gaussian_temporal_blend * temporal_gaussian_weight)
    final_score = type_prior * float(sim_score) * temporal_blend
    return {
        "objective": RERANK_OBJECTIVE_NAME,
        "semantic_score": float(sim_score),
        "temporal_gaussian_weight": float(temporal_gaussian_weight),
        "temporal_blend": float(temporal_blend),
        "type_prior": float(type_prior),
        "final_score": float(final_score),
    }


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

    scored: list[tuple[float, Document, dict[str, float | str]]] = []

    for doc, sim in docs_and_scores:
        doc_id = _doc_id(doc)
        if doc_id and doc_id in exclude_doc_ids:
            continue
        if doc.metadata.get("source_doc_id") in exclude_source_ids:
            continue

        objective_components = rerank_objective_score_components(
            sim_score=sim,
            doc_type=doc.metadata.get("type", ""),
            doc_ts_iso=doc.metadata.get("ts", ""),
            target=target,
            sigma_seconds=sigma_seconds,
        )
        scored.append((float(objective_components["final_score"]), doc, objective_components))

    scored.sort(key=lambda x: (-x[0], -_ts_epoch(x[1]), _card_rank(x[1]), _doc_id(x[1])))
    docs = [d for _, d, _ in scored[:top_k]]
    scored_candidates = [
        {
            "doc_id": _doc_id(doc),
            "doc_type": str(doc.metadata.get("type") or ""),
            "ts": str(doc.metadata.get("ts") or ""),
            **components,
        }
        for score, doc, components in scored
    ]

    near_tie_candidates: list[dict[str, float | str]] = []
    ambiguity_detected = False
    if scored:
        top_score = scored[0][0]
        near_tie = [(score, doc) for score, doc, _ in scored if (top_score - score) <= near_tie_delta]
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

    return RerankOutcome(
        docs=docs,
        ambiguity_detected=ambiguity_detected,
        near_tie_candidates=near_tie_candidates,
        scored_candidates=scored_candidates,
    )
