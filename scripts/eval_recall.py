#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

import arrow

from testbot.rerank import adaptive_sigma_fractional, similarity_with_time_and_type_score
from testbot.time_parse import parse_target_time as parse_target_time_shared


def parse_target_time(text: str, *, now: arrow.Arrow) -> arrow.Arrow:
    """Thin adapter to keep eval parsing aligned with runtime parser."""
    return parse_target_time_shared(text, now=now)


def candidate_score(candidate: dict, *, target: arrow.Arrow, sigma_seconds: float) -> float:
    """
    Thin adapter over runtime rerank scoring primitives.

    Intentionally simplified behavior: eval candidates are dicts from JSON fixtures instead
    of LangChain `Document` objects. This adapter only maps fixture field names to the runtime
    scoring function.
    """
    return similarity_with_time_and_type_score(
        sim_score=float(candidate["sim_score"]),
        doc_type=candidate.get("type", ""),
        doc_ts_iso=candidate.get("ts", ""),
        target=target,
        sigma_seconds=sigma_seconds,
    )


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate(cases: list[dict], *, top_k: int, idk_threshold: float, now: arrow.Arrow) -> dict:
    hit_count = 0
    memory_cases = 0
    ranks: list[int] = []
    idk_count = 0

    for case in cases:
        target = parse_target_time(case["utterance"], now=now)
        sigma = adaptive_sigma_fractional(now=now, target=target)
        ranked = sorted(
            case.get("candidates", []),
            key=lambda c: candidate_score(c, target=target, sigma_seconds=sigma),
            reverse=True,
        )

        top_score = candidate_score(ranked[0], target=target, sigma_seconds=sigma) if ranked else 0.0
        if top_score < idk_threshold:
            idk_count += 1

        if case.get("expected_intent") == "memory_lookup" and case.get("expected_doc_id"):
            memory_cases += 1
            expected = case["expected_doc_id"]
            ranked_ids = [c["doc_id"] for c in ranked]
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
        "fixed_now": now.isoformat(),
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
        load_cases(args.cases),
        top_k=args.top_k,
        idk_threshold=args.idk_threshold,
        now=fixed_now,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
