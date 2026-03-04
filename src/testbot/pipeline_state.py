from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from testbot.memory_cards import utc_now_iso

PIPELINE_SNAPSHOT_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class CandidateHit:
    doc_id: str
    score: float
    ts: str = ""
    card_type: str = ""


@dataclass(frozen=True)
class PipelineState:
    user_input: str
    rewritten_query: str = ""
    retrieval_candidates: list[CandidateHit] = field(default_factory=list)
    reranked_hits: list[CandidateHit] = field(default_factory=list)
    confidence_decision: dict[str, Any] = field(default_factory=dict)
    draft_answer: str = ""
    final_answer: str = ""
    invariant_decisions: dict[str, Any] = field(default_factory=dict)
    alignment_decision: dict[str, Any] = field(default_factory=dict)


def pipeline_state_to_dict(state: PipelineState) -> dict[str, Any]:
    return asdict(state)


def append_pipeline_snapshot(
    stage: str,
    state: PipelineState,
    *,
    log_path: Path = Path("./logs/session.jsonl"),
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": "pipeline_state_snapshot",
        "schema_version": PIPELINE_SNAPSHOT_SCHEMA_VERSION,
        "stage": stage,
        "state": pipeline_state_to_dict(state),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
