#!/usr/bin/env python3
"""Aggregate session JSONL events into per-turn analytics rows and KPI summary."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class TurnAnalytics:
    turn_index: int
    intent: str
    ambiguity_score: float
    action: str
    followup_proxy: float
    provenance_completeness: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("logs/session.jsonl"), help="Input JSONL event log path.")
    parser.add_argument("--output", type=Path, default=Path("logs/turn_analytics.jsonl"), help="Output per-turn analytics JSONL path.")
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("logs/turn_analytics_summary.json"),
        help="Output KPI summary JSON path.",
    )
    return parser.parse_args()


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _first_float(*values: object, default: float = 0.0) -> float:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
    return default


def _first_str(*values: object, default: str = "unknown") -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return default


def _provenance_completeness(row: dict[str, Any]) -> float:
    parts = 0
    if row.get("provenance_types"):
        parts += 1
    if row.get("used_memory_refs"):
        parts += 1
    if row.get("basis_statement"):
        parts += 1
    return round(parts / 3.0, 4)


def aggregate_turn_dataset(rows: Iterable[dict[str, Any]]) -> list[TurnAnalytics]:
    turns: list[TurnAnalytics] = []
    pending: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal pending
        if pending is None:
            return
        turns.append(
            TurnAnalytics(
                turn_index=len(turns) + 1,
                intent=_first_str(pending.get("intent"), default="unknown"),
                ambiguity_score=_first_float(pending.get("ambiguity_score"), default=0.0),
                action=_first_str(pending.get("action"), default="NONE"),
                followup_proxy=_first_float(pending.get("followup_proxy"), default=0.0),
                provenance_completeness=_first_float(pending.get("provenance_completeness"), default=0.0),
            )
        )
        pending = None

    for row in rows:
        event = str(row.get("event") or "")

        if event == "user_utterance_ingest":
            flush()
            pending = {
                "intent": "unknown",
                "ambiguity_score": 0.0,
                "action": "NONE",
                "followup_proxy": 0.0,
                "provenance_completeness": 0.0,
            }
            continue

        if pending is None:
            continue

        if event == "intent_classified":
            pending["intent"] = _first_str(row.get("intent"), pending.get("intent"), default="unknown")
            pending["ambiguity_score"] = _first_float(row.get("ambiguity_score"), pending.get("ambiguity_score"), default=0.0)
            pending["followup_proxy"] = _first_float(
                row.get("user_followup_signal_proxy"),
                pending.get("followup_proxy"),
                default=0.0,
            )
        elif event == "fallback_action_selected":
            pending["intent"] = _first_str(row.get("intent"), pending.get("intent"), default="unknown")
            pending["ambiguity_score"] = _first_float(row.get("ambiguity_score"), pending.get("ambiguity_score"), default=0.0)
            pending["action"] = _first_str(row.get("chosen_action"), pending.get("action"), default="NONE")
            pending["followup_proxy"] = _first_float(
                row.get("user_followup_signal_proxy"),
                pending.get("followup_proxy"),
                default=0.0,
            )
        elif event == "provenance_summary":
            pending["provenance_completeness"] = _provenance_completeness(row)

    flush()
    return turns


def compute_kpis(dataset: list[TurnAnalytics]) -> dict[str, float]:
    if not dataset:
        return {
            "grounded_answer_precision": 0.0,
            "false_knowing_rate": 0.0,
            "fallback_appropriateness": 0.0,
            "citation_completeness": 0.0,
            "turn_count": 0,
        }

    grounded_turns = [t for t in dataset if t.action == "NONE"]
    fallback_turns = [t for t in dataset if t.action != "NONE"]
    grounded_prec = sum(1 for t in grounded_turns if t.provenance_completeness >= 0.66) / max(len(grounded_turns), 1)
    false_knowing = sum(1 for t in grounded_turns if t.provenance_completeness == 0.0) / max(len(grounded_turns), 1)
    fallback_ok = sum(1 for t in fallback_turns if t.followup_proxy >= 0.5) / max(len(fallback_turns), 1)
    citation_complete = sum(t.provenance_completeness for t in dataset) / len(dataset)
    return {
        "grounded_answer_precision": round(grounded_prec, 4),
        "false_knowing_rate": round(false_knowing, 4),
        "fallback_appropriateness": round(fallback_ok, 4),
        "citation_completeness": round(citation_complete, 4),
        "turn_count": len(dataset),
    }


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = _resolve_path(args.input)
    output_path = _resolve_path(args.output)
    summary_path = _resolve_path(args.summary_output)

    rows = _read_jsonl(input_path)
    dataset = aggregate_turn_dataset(rows)
    kpis = compute_kpis(dataset)

    _write_jsonl(output_path, [turn.__dict__ for turn in dataset])
    _write_json(summary_path, kpis)

    print(json.dumps({"dataset_path": str(output_path), "summary_path": str(summary_path), "kpis": kpis}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
