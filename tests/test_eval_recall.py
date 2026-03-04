from __future__ import annotations

import json
import os
import subprocess


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

    attribution = metrics["objective_component_attribution"]
    assert "average_top_candidate_components" in attribution
    assert "per_case" in attribution
    assert len(attribution["per_case"]) == metrics["cases_total"]
