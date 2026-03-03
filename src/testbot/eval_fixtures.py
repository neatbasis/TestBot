from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    utterance: str
    expected_intent: str
    expected_doc_id: str | None
    candidates: tuple[dict[str, Any], ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_eval_cases(path: Path | None = None) -> list[EvalCase]:
    cases_path = path or _repo_root() / "eval" / "cases.jsonl"
    loaded: list[EvalCase] = []
    with cases_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            loaded.append(
                EvalCase(
                    case_id=payload["case_id"],
                    utterance=payload["utterance"],
                    expected_intent=payload["expected_intent"],
                    expected_doc_id=payload["expected_doc_id"],
                    candidates=tuple(payload["candidates"]),
                )
            )
    return loaded


def cases_by_id(path: Path | None = None) -> dict[str, EvalCase]:
    return {case.case_id: case for case in load_eval_cases(path)}


def is_iso_timestamp(value: str) -> bool:
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return True


def best_candidate_doc_id(case: EvalCase, score_threshold: float = 0.5) -> str | None:
    if case.expected_intent == "dont_know_from_memory":
        return None
    if case.expected_doc_id and any(candidate["doc_id"] == case.expected_doc_id for candidate in case.candidates):
        return case.expected_doc_id
    eligible = [candidate for candidate in case.candidates if candidate["sim_score"] >= score_threshold]
    if not eligible:
        return None
    return max(eligible, key=lambda candidate: candidate["sim_score"])["doc_id"]
