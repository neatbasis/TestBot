#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import arrow
from langchain_core.documents import Document

from testbot.eval_fixtures import EvalCase, load_eval_cases
from testbot.rerank import (
    adaptive_sigma_fractional,
    rerank_docs_with_time_and_type,
    similarity_with_time_and_type_score,
)
from testbot.time_parse import parse_target_time as parse_target_time_shared

# Non-goals:
# - This eval keeps fixture-driven candidate pools; it does not try to replicate online retrieval.
# - This eval reports recall/IDK metrics only; it does not emulate generation-time fallback wording.


def _as_arrow(value: arrow.Arrow | datetime | str) -> arrow.Arrow:
    """Adapter for type differences only (datetime/str -> Arrow)."""
    if isinstance(value, arrow.Arrow):
        return value
    return arrow.get(value)


def parse_target_time(text: str, *, now: arrow.Arrow | datetime | str) -> arrow.Arrow:
    """Thin adapter to keep eval parsing aligned with runtime parser."""
    return parse_target_time_shared(text, now=_as_arrow(now))


def _candidate_to_document(candidate: dict[str, Any]) -> Document:
    return Document(
        id=candidate.get("doc_id", ""),
        page_content=candidate.get("text", ""),
        metadata={
            "doc_id": candidate.get("doc_id", ""),
            "type": candidate.get("type", ""),
            "ts": candidate.get("ts", ""),
            "source_doc_id": candidate.get("source_doc_id", ""),
        },
    )


def rank_candidates(
    candidates: list[dict[str, Any]],
    *,
    now: arrow.Arrow | datetime | str,
    target: arrow.Arrow,
    sigma_seconds: float,
) -> list[dict[str, Any]]:
    now_arrow = _as_arrow(now)
    docs_and_scores = [(_candidate_to_document(candidate), float(candidate.get("sim_score", 0.0))) for candidate in candidates]
    ranked_docs = rerank_docs_with_time_and_type(
        docs_and_scores,
        now=now_arrow,
        target=target,
        sigma_seconds=sigma_seconds,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        top_k=len(candidates),
    )
    candidates_by_doc_id = {candidate["doc_id"]: candidate for candidate in candidates}
    return [candidates_by_doc_id.get((doc.id or ""), {"doc_id": (doc.id or "")}) for doc in ranked_docs]


def candidate_score(candidate: dict[str, Any], *, target: arrow.Arrow, sigma_seconds: float) -> float:
    return similarity_with_time_and_type_score(
        sim_score=float(candidate.get("sim_score", 0.0)),
        doc_type=str(candidate.get("type", "")),
        doc_ts_iso=str(candidate.get("ts", "")),
        target=target,
        sigma_seconds=sigma_seconds,
    )


def evaluate(cases: list[EvalCase], *, top_k: int, idk_threshold: float, now: arrow.Arrow | datetime | str) -> dict:
    now_arrow = _as_arrow(now)
    hit_count = 0
    memory_cases = 0
    ranks: list[int] = []
    idk_count = 0

    for case in cases:
        target = parse_target_time(case.utterance, now=now_arrow)
        sigma = adaptive_sigma_fractional(now=now_arrow, target=target)
        ranked = rank_candidates(
            list(case.candidates),
            now=now_arrow,
            target=target,
            sigma_seconds=sigma,
        )

        top_score = candidate_score(ranked[0], target=target, sigma_seconds=sigma) if ranked else 0.0
        if top_score < idk_threshold:
            idk_count += 1

        if case.expected_intent == "memory_lookup" and case.expected_doc_id:
            memory_cases += 1
            expected = case.expected_doc_id
            ranked_ids = [c.get("doc_id", "") for c in ranked]
            rank = ranked_ids.index(expected) + 1 if expected in ranked_ids else len(ranked_ids) + 1
            ranks.append(rank)
            if rank <= top_k:
                hit_count += 1

    return {
        "cases_total": len(cases),
        "memory_lookup_cases": memory_cases,
        "hit_at_k": (hit_count / memory_cases) if memory_cases else 0.0,
        "average_rank_expected_memory": mean(ranks) if ranks else None,
        "dont_know_from_memory_decisions": idk_count,
        "top_k": top_k,
        "idk_threshold": idk_threshold,
        "fixed_now": now_arrow.isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("eval/cases.jsonl"))
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--idk-threshold", type=float, default=0.2)
    parser.add_argument("--now", default="2026-03-10T11:00:00+00:00")
    args = parser.parse_args()

    fixed_now = arrow.get(args.now)
    metrics = evaluate(
        load_eval_cases(args.cases),
        top_k=args.top_k,
        idk_threshold=args.idk_threshold,
        now=fixed_now,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
