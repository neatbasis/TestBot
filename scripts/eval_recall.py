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
    RerankOutcome,
    adaptive_sigma_fractional,
    has_sufficient_context_confidence_from_objective,
    load_rerank_objective_config,
    rerank_docs_with_time_and_type_outcome,
    rerank_objective_score_components,
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
    return rank_candidates_with_signals(
        candidates,
        now=now,
        target=target,
        sigma_seconds=sigma_seconds,
    )["ranked_candidates"]


def rank_candidates_with_signals(
    candidates: list[dict[str, Any]],
    *,
    now: arrow.Arrow | datetime | str,
    target: arrow.Arrow,
    sigma_seconds: float,
    near_tie_delta: float = 0.02,
    context_confidence_min_similarity: float = 0.35,
) -> dict[str, Any]:
    now_arrow = _as_arrow(now)
    docs_and_scores = [(_candidate_to_document(candidate), float(candidate.get("sim_score", 0.0))) for candidate in candidates]
    outcome: RerankOutcome = rerank_docs_with_time_and_type_outcome(
        docs_and_scores,
        now=now_arrow,
        target=target,
        sigma_seconds=sigma_seconds,
        exclude_doc_ids=set(),
        exclude_source_ids=set(),
        top_k=len(candidates),
        near_tie_delta=near_tie_delta,
    )
    candidates_by_doc_id = {candidate["doc_id"]: candidate for candidate in candidates}
    ranked_candidates = [candidates_by_doc_id.get((doc.id or ""), {"doc_id": (doc.id or "")}) for doc in outcome.docs]
    del context_confidence_min_similarity
    context_confident = has_sufficient_context_confidence_from_objective(
        scored_candidates=outcome.scored_candidates,
        ambiguity_detected=outcome.ambiguity_detected,
    )
    return {
        "ranked_candidates": ranked_candidates,
        "ambiguity_detected": outcome.ambiguity_detected,
        "near_tie_candidates": outcome.near_tie_candidates,
        "scored_candidates": outcome.scored_candidates,
        "context_confident": context_confident,
    }


def candidate_objective_components(
    candidate: dict[str, Any],
    *,
    target: arrow.Arrow,
    sigma_seconds: float,
) -> dict[str, float | str]:
    return rerank_objective_score_components(
        sim_score=float(candidate.get("sim_score", 0.0)),
        doc_type=str(candidate.get("type", "")),
        doc_ts_iso=str(candidate.get("ts", "")),
        target=target,
        sigma_seconds=sigma_seconds,
    )


def evaluate(
    cases: list[EvalCase],
    *,
    top_k: int,
    idk_threshold: float,
    now: arrow.Arrow | datetime | str,
) -> dict:
    now_arrow = _as_arrow(now)
    objective_config = load_rerank_objective_config(force_reload=True)
    hit_count = 0
    memory_cases = 0
    ranks: list[int] = []
    idk_count = 0
    component_totals = {
        "semantic_score": 0.0,
        "temporal_gaussian_weight": 0.0,
        "temporal_blend": 0.0,
        "type_prior": 0.0,
        "final_score": 0.0,
    }
    attribution_count = 0
    case_attribution: list[dict[str, Any]] = []

    for case in cases:
        target = parse_target_time(case.utterance, now=now_arrow)
        sigma = adaptive_sigma_fractional(now=now_arrow, target=target)
        ranked = rank_candidates(
            list(case.candidates),
            now=now_arrow,
            target=target,
            sigma_seconds=sigma,
        )

        top_components = (
            candidate_objective_components(ranked[0], target=target, sigma_seconds=sigma)
            if ranked
            else {
                "semantic_score": 0.0,
                "temporal_gaussian_weight": 0.0,
                "temporal_blend": 0.0,
                "type_prior": 0.0,
                "final_score": 0.0,
            }
        )
        top_score = float(top_components["final_score"])
        if top_score < idk_threshold:
            idk_count += 1

        attribution_count += 1
        for key in component_totals:
            component_totals[key] += float(top_components.get(key, 0.0))

        expected_components: dict[str, float | str] | None = None
        if case.expected_doc_id:
            expected_candidate = next((c for c in ranked if c.get("doc_id") == case.expected_doc_id), None)
            if expected_candidate is not None:
                expected_components = candidate_objective_components(expected_candidate, target=target, sigma_seconds=sigma)

        case_attribution.append(
            {
                "case_id": case.case_id,
                "utterance": case.utterance,
                "top_doc_id": ranked[0].get("doc_id", "") if ranked else "",
                "expected_doc_id": case.expected_doc_id,
                "top_objective": top_components,
                "expected_objective": expected_components,
            }
        )

        if case.expected_intent == "memory_lookup" and case.expected_doc_id:
            memory_cases += 1
            expected = case.expected_doc_id
            ranked_ids = [c.get("doc_id", "") for c in ranked]
            rank = ranked_ids.index(expected) + 1 if expected in ranked_ids else len(ranked_ids) + 1
            ranks.append(rank)
            if rank <= top_k:
                hit_count += 1

    avg_attribution = {
        key: (value / attribution_count) if attribution_count else 0.0 for key, value in component_totals.items()
    }

    return {
        "cases_total": len(cases),
        "memory_lookup_cases": memory_cases,
        "hit_at_k": (hit_count / memory_cases) if memory_cases else 0.0,
        "average_rank_expected_memory": mean(ranks) if ranks else None,
        "dont_know_from_memory_decisions": idk_count,
        "top_k": top_k,
        "idk_threshold": idk_threshold,
        "fixed_now": now_arrow.isoformat(),
        "objective": f"{objective_config.objective_name}_{objective_config.objective_version}",
        "objective_version": objective_config.objective_version,
        "objective_component_attribution": {
            "average_top_candidate_components": avg_attribution,
            "per_case": case_attribution,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("eval/cases.jsonl"))
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--idk-threshold", type=float, default=0.2)
    parser.add_argument("--now", default="2026-03-10T11:00:00+00:00")
    parser.add_argument(
        "--objective-config",
        type=Path,
        default=None,
        help="Optional path to a rerank objective config JSON.",
    )
    parser.add_argument(
        "--compare-objective-config",
        action="append",
        type=Path,
        default=[],
        help="Optional additional rerank objective config paths to compare against baseline.",
    )
    args = parser.parse_args()

    import os

    fixed_now = arrow.get(args.now)
    cases = load_eval_cases(args.cases)

    original_config = os.getenv("TESTBOT_RERANK_OBJECTIVE_CONFIG")

    def _set_config(path: Path | None) -> None:
        if path is None:
            os.environ.pop("TESTBOT_RERANK_OBJECTIVE_CONFIG", None)
            return
        os.environ["TESTBOT_RERANK_OBJECTIVE_CONFIG"] = str(path)

    try:
        _set_config(args.objective_config)
        baseline_metrics = evaluate(
            cases,
            top_k=args.top_k,
            idk_threshold=args.idk_threshold,
            now=fixed_now,
        )

        comparison_metrics: list[dict[str, Any]] = []
        baseline_hit = float(baseline_metrics["hit_at_k"])
        baseline_idk = int(baseline_metrics["dont_know_from_memory_decisions"])

        for compare_path in args.compare_objective_config:
            _set_config(compare_path)
            candidate_metrics = evaluate(
                cases,
                top_k=args.top_k,
                idk_threshold=args.idk_threshold,
                now=fixed_now,
            )
            comparison_metrics.append(
                {
                    "config_path": str(compare_path),
                    "objective": candidate_metrics["objective"],
                    "objective_version": candidate_metrics["objective_version"],
                    "hit_at_k": candidate_metrics["hit_at_k"],
                    "hit_at_k_delta_vs_baseline": float(candidate_metrics["hit_at_k"]) - baseline_hit,
                    "dont_know_from_memory_decisions": candidate_metrics["dont_know_from_memory_decisions"],
                    "idk_delta_vs_baseline": int(candidate_metrics["dont_know_from_memory_decisions"]) - baseline_idk,
                }
            )

        baseline_metrics["objective_version_comparison"] = comparison_metrics
    finally:
        if original_config is None:
            os.environ.pop("TESTBOT_RERANK_OBJECTIVE_CONFIG", None)
        else:
            os.environ["TESTBOT_RERANK_OBJECTIVE_CONFIG"] = original_config

    print(json.dumps(baseline_metrics, indent=2))


if __name__ == "__main__":
    main()
