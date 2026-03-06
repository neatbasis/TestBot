from __future__ import annotations

import json
import os
import subprocess
import importlib.util
from pathlib import Path

import arrow

_EVAL_RECALL_PATH = Path(__file__).resolve().parents[1] / "scripts" / "eval_recall.py"
_eval_spec = importlib.util.spec_from_file_location("eval_recall", _EVAL_RECALL_PATH)
assert _eval_spec and _eval_spec.loader
eval_recall = importlib.util.module_from_spec(_eval_spec)
_eval_spec.loader.exec_module(eval_recall)


def test_eval_reports_objective_component_attribution() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    out = subprocess.run(
        ["python", "scripts/eval_recall.py", "--now", "2026-03-10T11:00:00+00:00"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    metrics = json.loads(out.stdout)

    assert metrics["objective_version"] == "v1"
    attribution = metrics["objective_component_attribution"]
    assert "average_top_candidate_components" in attribution
    assert "per_case" in attribution
    assert len(attribution["per_case"]) == metrics["cases_total"]


def test_rank_candidates_with_signals_emits_runtime_comparable_fields() -> None:
    now = arrow.get("2026-03-10T11:00:00+00:00")
    target = eval_recall.parse_target_time("What did I say 3 hours ago about medication?", now=now)
    sigma = eval_recall.adaptive_sigma_fractional(now=now, target=target)
    candidates = [
        {"doc_id": "a", "sim_score": 0.62, "type": "user_utterance", "ts": "2026-03-10T08:00:00+00:00"},
        {"doc_id": "b", "sim_score": 0.62, "type": "user_utterance", "ts": "2026-03-10T08:00:00+00:00"},
    ]

    signals = eval_recall.rank_candidates_with_signals(candidates, now=now, target=target, sigma_seconds=sigma)

    assert [c["doc_id"] for c in signals["ranked_candidates"]] == ["a", "b"]
    assert signals["ambiguity_detected"] is False
    assert len(signals["near_tie_candidates"]) >= 2
    assert [c["doc_id"] for c in signals["scored_candidates"]] == ["a", "b"]
    assert signals["context_confident"] is True


def test_eval_compare_objective_versions_reports_deltas(tmp_path) -> None:
    compare_config = tmp_path / "rerank_objective_v2.json"
    compare_config.write_text(
        json.dumps(
            {
                "objective_name": "semantic_temporal_type",
                "objective_version": "v2",
                "coefficients": {
                    "base_temporal_blend": 0.5,
                    "gaussian_temporal_blend": 0.5,
                    "reflection_type_prior": 0.8,
                    "default_type_prior": 1.0,
                },
                "confidence_thresholds": {
                    "top_final_score_min": 0.2,
                    "min_margin_to_second": 0.0,
                    "allow_ambiguity_override": False,
                    "ambiguity_override_top_final_score_min": 0.6,
                },
            }
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    out = subprocess.run(
        [
            "python",
            "scripts/eval_recall.py",
            "--now",
            "2026-03-10T11:00:00+00:00",
            "--compare-objective-config",
            str(compare_config),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    metrics = json.loads(out.stdout)

    assert metrics["objective"] == "semantic_temporal_type_v1"
    comparisons = metrics["objective_version_comparison"]
    assert len(comparisons) == 1
    assert comparisons[0]["objective_version"] == "v2"
    assert "hit_at_k_delta_vs_baseline" in comparisons[0]


def test_eval_parse_target_time_supports_ambiguous_phrase_boundaries() -> None:
    now = arrow.get("2026-03-10T11:00:00+00:00")

    assert eval_recall.parse_target_time("What did I mention earlier this week?", now=now) == now.floor("week")
    assert eval_recall.parse_target_time("What did I mention this morning?", now=now) == now.floor("day").shift(hours=+9)
    assert eval_recall.parse_target_time("What did I mention recently?", now=now) == now.shift(hours=-6)


def test_eval_recall_fixtures_include_temporal_boundary_cases() -> None:
    cases = eval_recall.load_eval_cases(Path("eval/cases.jsonl"))
    case_ids = {case.case_id for case in cases}

    assert "morning-hydration-boundary" in case_ids
    assert "recently-symptom-note" in case_ids
