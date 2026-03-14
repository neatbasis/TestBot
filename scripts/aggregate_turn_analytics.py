#!/usr/bin/env python3
"""Aggregate session JSONL events into per-turn analytics rows and KPI summary."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from testbot.turn_analytics_diagnostics import build_coverage_diagnostics as _build_coverage_diagnostics

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class TurnAnalytics:
    turn_index: int
    intent: str
    ambiguity_score: float
    action: str
    followup_proxy: float
    provenance_completeness: float


SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3}
ANALYTICS_EVENTS = {
    "user_utterance_ingest",
    "intent_classified",
    "fallback_action_selected",
    "provenance_summary",
}


@dataclass
class ValidationSummary:
    invalid_rows: int = 0
    skipped_rows: int = 0
    per_event_validation_failures: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.per_event_validation_failures is None:
            self.per_event_validation_failures = {}

    def register_failure(self, event: str) -> None:
        self.invalid_rows += 1
        self.skipped_rows += 1
        self.per_event_validation_failures[event] = self.per_event_validation_failures.get(event, 0) + 1



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


def _validate_analytics_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    event = row.get("event")
    if not isinstance(event, str):
        return ["key 'event' must be str"]

    schema_version = row.get("schema_version", 1)
    if not isinstance(schema_version, int):
        errors.append("key 'schema_version' expected int when present")
    elif schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"unsupported schema_version '{schema_version}'")

    if event not in ANALYTICS_EVENTS:
        return errors

    required_by_event: dict[str, dict[str, tuple[type, ...]]] = {
        "user_utterance_ingest": {
            "utterance": (str,),
        },
        "intent_classified": {
            "intent": (str,),
            "ambiguity_score": (int, float),
            "user_followup_signal_proxy": (int, float),
        },
        "fallback_action_selected": {
            "intent": (str,),
            "ambiguity_score": (int, float),
            "chosen_action": (str,),
            "user_followup_signal_proxy": (int, float),
        },
        "provenance_summary": {
            "provenance_types": (list,),
            "used_memory_refs": (list,),
            "basis_statement": (str,),
        },
    }

    for key, expected_types in required_by_event[event].items():
        if key not in row:
            errors.append(f"missing required key '{key}'")
            continue
        if not isinstance(row[key], expected_types):
            expected_names = "|".join(t.__name__ for t in expected_types)
            errors.append(f"key '{key}' expected {expected_names}, got {type(row[key]).__name__}")

    return errors


def normalize_and_validate_rows(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], ValidationSummary]:
    normalized_rows: list[dict[str, Any]] = []
    summary = ValidationSummary()
    for row in rows:
        normalized = dict(row)
        if "schema_version" not in normalized:
            normalized["schema_version"] = 1

        errors = _validate_analytics_row(normalized)
        if errors and isinstance(normalized.get("event"), str) and normalized["event"] in ANALYTICS_EVENTS:
            summary.register_failure(normalized["event"])
            continue
        normalized_rows.append(normalized)

    return normalized_rows, summary


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




def build_coverage_diagnostics(rows: Iterable[dict[str, Any]]):
    return _build_coverage_diagnostics(rows, ANALYTICS_EVENTS)

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




def compute_alignment_dimension_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    sums: dict[str, float] = {}
    applicable_counts: dict[str, int] = {}
    not_applicable_counts: dict[str, int] = {}

    for row in rows:
        if row.get("event") != "alignment_decision_evaluated":
            continue
        dimensions = row.get("alignment_dimensions")
        if not isinstance(dimensions, dict):
            continue

        for name, value in dimensions.items():
            if isinstance(value, (int, float)):
                sums[name] = sums.get(name, 0.0) + float(value)
                applicable_counts[name] = applicable_counts.get(name, 0) + 1
            elif isinstance(value, str) and value == "not_applicable":
                not_applicable_counts[name] = not_applicable_counts.get(name, 0) + 1

    averages = {
        name: round(sums[name] / applicable_counts[name], 4)
        for name in sorted(sums)
        if applicable_counts.get(name, 0) > 0
    }
    return {
        "alignment_dimension_averages": averages,
        "alignment_dimension_applicable_counts": dict(sorted(applicable_counts.items())),
        "alignment_dimension_not_applicable_counts": dict(sorted(not_applicable_counts.items())),
    }


def evaluate_categorical_falsifiability(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate minimal, log-witnessed falsifiability checks for categorical claims.

    The checks intentionally stay operational: each law claim must have a concrete
    witness in turn events and commit payloads.
    """

    turns: list[list[dict[str, Any]]] = []
    current_turn: list[dict[str, Any]] = []

    for row in rows:
        event = str(row.get("event") or "")
        if event == "user_utterance_ingest":
            if current_turn:
                turns.append(current_turn)
            current_turn = [row]
            continue
        if current_turn:
            current_turn.append(row)

    if current_turn:
        turns.append(current_turn)

    violations: list[dict[str, Any]] = []

    for index, turn_rows in enumerate(turns, start=1):
        fallback = next((r for r in turn_rows if r.get("event") == "fallback_action_selected"), None)
        commit = next((r for r in turn_rows if r.get("event") == "commit_stage_recorded"), None)
        intent = next((r for r in turn_rows if r.get("event") == "intent_classified"), None)
        provenance = next((r for r in turn_rows if r.get("event") == "provenance_summary"), None)

        chosen_action = str((fallback or {}).get("chosen_action") or "")

        # Law 1: local-repair confinement in fiber (no global jump repair).
        if chosen_action == "CONTINUE_REPAIR_RECONSTRUCTION":
            pending_repair = (commit or {}).get("pending_repair_state") if isinstance(commit, dict) else None
            remaining_obligations = (commit or {}).get("remaining_obligations") if isinstance(commit, dict) else None
            local_commit_witness = (
                isinstance(pending_repair, dict)
                and bool(pending_repair.get("repair_required_by_policy") or pending_repair.get("repair_offered_to_user"))
            ) or (isinstance(remaining_obligations, list) and "continue_repair_reconstruction" in remaining_obligations)

            if not local_commit_witness:
                violations.append(
                    {
                        "turn_index": index,
                        "law": "local_repair_confinement",
                        "message": "repair continuation action lacked same-turn committed repair witness",
                    }
                )

        # Law 2: justified transport witness for continuity evidence.
        continuity_evidence = (commit or {}).get("retrieval_continuity_evidence") if isinstance(commit, dict) else None
        if isinstance(continuity_evidence, list) and continuity_evidence:
            used_memory_refs = (provenance or {}).get("used_memory_refs") if isinstance(provenance, dict) else None
            basis_statement = str((provenance or {}).get("basis_statement") or "") if isinstance(provenance, dict) else ""
            if not (isinstance(used_memory_refs, list) and used_memory_refs and basis_statement.strip()):
                violations.append(
                    {
                        "turn_index": index,
                        "law": "justified_transport",
                        "message": "continuity transport lacked provenance witness (used_memory_refs + basis_statement)",
                    }
                )

        # Law 3: reindexing coherence between intent.resolve and policy.decide telemetry.
        intent_label = str((intent or {}).get("intent") or "")
        fallback_intent = str((fallback or {}).get("intent") or "")
        if intent_label and fallback_intent and intent_label != fallback_intent:
            violations.append(
                {
                    "turn_index": index,
                    "law": "reindexing_coherence",
                    "message": "intent_classified.intent diverged from fallback_action_selected.intent",
                }
            )

    observed_case_counts = {
        "local_repair_confinement": sum(
            1
            for turn_rows in turns
            if str(next((r for r in turn_rows if r.get("event") == "fallback_action_selected"), {}).get("chosen_action") or "")
            == "CONTINUE_REPAIR_RECONSTRUCTION"
        ),
        "justified_transport": sum(
            1
            for turn_rows in turns
            if isinstance(next((r for r in turn_rows if r.get("event") == "commit_stage_recorded"), {}).get("retrieval_continuity_evidence"), list)
            and bool(next((r for r in turn_rows if r.get("event") == "commit_stage_recorded"), {}).get("retrieval_continuity_evidence"))
        ),
        "reindexing_coherence": sum(
            1
            for turn_rows in turns
            if bool(next((r for r in turn_rows if r.get("event") == "intent_classified"), {}).get("intent"))
            and bool(next((r for r in turn_rows if r.get("event") == "fallback_action_selected"), {}).get("intent"))
        ),
    }

    checks = {
        "local_repair_confinement": not any(v["law"] == "local_repair_confinement" for v in violations),
        "justified_transport": not any(v["law"] == "justified_transport" for v in violations),
        "reindexing_coherence": not any(v["law"] == "reindexing_coherence" for v in violations),
    }
    vacuous_checks = [law for law, count in observed_case_counts.items() if count == 0]

    return {
        "checks": checks,
        "violations": violations,
        "violating_turn_count": len({v["turn_index"] for v in violations}),
        "checked_turn_count": len(turns),
        "observed_case_counts": observed_case_counts,
        "vacuous_checks": vacuous_checks,
        "pass": not violations,
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
    normalized_rows, validation_summary = normalize_and_validate_rows(rows)
    coverage = build_coverage_diagnostics(normalized_rows)
    dataset = aggregate_turn_dataset(normalized_rows)
    kpis = compute_kpis(dataset)
    alignment_dimension_summary = compute_alignment_dimension_summary(normalized_rows)
    falsifiability_summary = evaluate_categorical_falsifiability(normalized_rows)
    summary_payload = {
        **kpis,
        **alignment_dimension_summary,
        "categorical_falsifiability": falsifiability_summary,
        "invalid_rows": validation_summary.invalid_rows,
        "skipped_rows": validation_summary.skipped_rows,
        "per_event_validation_failures": validation_summary.per_event_validation_failures,
        "input_rows_total": coverage.input_rows_total,
        "recognized_analytics_rows": coverage.recognized_analytics_rows,
        "ignored_non_analytics_rows": coverage.ignored_non_analytics_rows,
        "turn_start_events": coverage.turn_start_events,
        "ignored_event_counts": coverage.ignored_event_counts,
        "warnings": coverage.warnings,
    }

    _write_jsonl(output_path, [turn.__dict__ for turn in dataset])
    _write_json(summary_path, summary_payload)

    for warning in coverage.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    print(json.dumps({"dataset_path": str(output_path), "summary_path": str(summary_path), "kpis": summary_payload}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
