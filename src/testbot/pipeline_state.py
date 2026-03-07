from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from testbot.memory_cards import utc_now_iso

PIPELINE_SNAPSHOT_SCHEMA_VERSION = 3


@dataclass(frozen=True)
class CandidateHit:
    doc_id: str
    score: float
    ts: str = ""
    card_type: str = ""


class ProvenanceType(StrEnum):
    MEMORY = "MEMORY"
    CHAT_HISTORY = "CHAT_HISTORY"
    SYSTEM_STATE = "SYSTEM_STATE"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PipelineState:
    user_input: str
    rewritten_query: str = ""
    retrieval_candidates: list[CandidateHit] = field(default_factory=list)
    reranked_hits: list[CandidateHit] = field(default_factory=list)
    confidence_decision: dict[str, Any] = field(default_factory=dict)
    draft_answer: str = ""
    final_answer: str = ""
    claims: list[str] = field(default_factory=list)
    provenance_types: list[ProvenanceType] = field(default_factory=list)
    used_memory_refs: list[str] = field(default_factory=list)
    used_source_evidence_refs: list[str] = field(default_factory=list)
    source_evidence_attribution: list[dict[str, str]] = field(default_factory=list)
    basis_statement: str = ""
    invariant_decisions: dict[str, Any] = field(default_factory=dict)
    alignment_decision: dict[str, Any] = field(default_factory=dict)
    last_user_message_ts: str = ""
    classified_intent: str = ""
    resolved_intent: str = ""
    prior_unresolved_intent: str = ""
    response_plan: dict[str, Any] = field(default_factory=dict)


def pipeline_state_to_dict(state: PipelineState) -> dict[str, Any]:
    payload = asdict(state)
    payload["provenance_types"] = [p.value for p in state.provenance_types]
    return payload


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
