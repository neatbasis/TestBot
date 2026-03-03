#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import mean


_DURATION_RE = re.compile(r"\b(?P<num>\d+)\s*(?P<unit>hour|hours|day|days|week|weeks|minute|minutes)\b")


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts).astimezone(UTC)


def parse_target_time(text: str, *, now: datetime) -> datetime:
    low = text.lower()

    if "last night" in low:
        return now - timedelta(hours=12)
    if "earlier this week" in low:
        return now - timedelta(days=3)

    m = _DURATION_RE.search(low)
    if m:
        qty = int(m.group("num"))
        unit = m.group("unit")
        if unit.startswith("minute"):
            delta = timedelta(minutes=qty)
        elif unit.startswith("hour"):
            delta = timedelta(hours=qty)
        elif unit.startswith("day"):
            delta = timedelta(days=qty)
        else:
            delta = timedelta(weeks=qty)

        if "ago" in low or "earlier" in low:
            return now - delta
        if "from now" in low or "in " in low:
            return now + delta

    return now


def adaptive_sigma_fractional(*, now: datetime, target: datetime, frac: float = 0.25) -> float:
    sigma_min = 10 * 60
    sigma_max = 30 * 24 * 3600
    d = abs((target - now).total_seconds())
    sigma = frac * d
    return max(sigma_min, min(sigma, sigma_max))


def time_weight(doc_ts_iso: str, target: datetime, sigma_seconds: float) -> float:
    try:
        ts = parse_iso(doc_ts_iso)
        dt = (ts - target).total_seconds()
        return math.exp(-(dt * dt) / (2.0 * sigma_seconds * sigma_seconds))
    except Exception:
        return 0.0


def combined_score(candidate: dict, *, target: datetime, sigma_seconds: float) -> float:
    type_prior = 0.7 if candidate.get("type") == "reflection" else 1.0
    sim = float(candidate["sim_score"])
    tw = time_weight(candidate.get("ts", ""), target, sigma_seconds)
    return type_prior * sim * (0.25 + 0.75 * tw)


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate(cases: list[dict], *, top_k: int, idk_threshold: float, now: datetime) -> dict:
    hit_count = 0
    memory_cases = 0
    ranks: list[int] = []
    idk_count = 0

    for case in cases:
        target = parse_target_time(case["utterance"], now=now)
        sigma = adaptive_sigma_fractional(now=now, target=target)
        ranked = sorted(
            case.get("candidates", []),
            key=lambda c: combined_score(c, target=target, sigma_seconds=sigma),
            reverse=True,
        )

        top_score = combined_score(ranked[0], target=target, sigma_seconds=sigma) if ranked else 0.0
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

    metrics = evaluate(
        load_cases(args.cases),
        top_k=args.top_k,
        idk_threshold=args.idk_threshold,
        now=parse_iso(args.now),
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
