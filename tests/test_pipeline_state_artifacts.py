from __future__ import annotations

import json
from dataclasses import dataclass

from testbot.pipeline_state import (
    AlignmentDecision,
    ConfidenceDecision,
    InvariantDecision,
    PipelineState,
    ResponsePlanArtifact,
    append_pipeline_snapshot,
    pipeline_state_to_dict,
)


def test_pipeline_state_coerces_legacy_dicts_to_typed_stage_artifacts() -> None:
    state = PipelineState(
        user_input="hello",
        confidence_decision={"context_confident": True, "z_key": "z", "a_key": "a"},
        invariant_decisions={"answer_mode": "assist", "fallback_action": "ANSWER_GENERAL_KNOWLEDGE"},
        alignment_decision={"final_alignment_decision": "allow", "dimensions": {"safety": "pass"}},
        response_plan={"pathway": "non_memory", "stages": [{"name": "Observation", "objective": "Observe."}]},
    )

    assert isinstance(state.confidence_decision, ConfidenceDecision)
    assert isinstance(state.invariant_decisions, InvariantDecision)
    assert isinstance(state.alignment_decision, AlignmentDecision)
    assert isinstance(state.response_plan, ResponsePlanArtifact)

    assert state.confidence_decision["context_confident"] is True
    assert state.confidence_decision.get("z_key") == "z"
    assert state.confidence_decision.get("a_key") == "a"


def test_pipeline_state_to_dict_contains_new_stage_contract_fields_deterministically() -> None:
    state = PipelineState(
        user_input="hello",
        candidate_facts={"facts": [{"claim": "x"}]},
        resolved_context={"entities": [{"name": "satellite"}], "time_window": {"start": "2026-03-01"}},
        evidence_bundle={"memory_refs": ["mem-1"]},
        policy_decision={"policy": "answer", "decision": "allow"},
        validation_result={"passed": True},
        render_output={"rendered_text": "final output"},
        commit_receipt={"committed": True, "commit_id": "abc123"},
        same_turn_exclusion={"excluded_doc_ids": ["doc-1"], "reason": "already cited"},
        pending_repair={"required": True, "reason": "missing provenance"},
        pending_clarification={"required": True, "question": "Can you narrow the timeframe?"},
    )

    payload = pipeline_state_to_dict(state)
    assert payload["candidate_facts"]["facts"] == [{"claim": "x"}]
    assert payload["pending_repair"] == {"reason": "missing provenance", "required": True}

    confidence = PipelineState(user_input="x", confidence_decision={"z_key": 1, "a_key": 2})
    confidence_payload = pipeline_state_to_dict(confidence)
    assert list(confidence_payload["confidence_decision"].keys()) == ["a_key", "z_key"]


def test_append_pipeline_snapshot_writes_serialized_stage_contracts(tmp_path) -> None:
    path = tmp_path / "session.jsonl"
    state = PipelineState(
        user_input="hello",
        confidence_decision={"context_confident": False},
        pending_clarification={"required": True, "question": "Which Friday?"},
    )

    append_pipeline_snapshot("answer", state, log_path=path)

    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["schema_version"] == 3
    assert isinstance(row["ts"], str)
    assert row["state"]["pending_clarification"] == {"question": "Which Friday?", "required": True}


@dataclass(frozen=True)
class _FixedSnapshotClock:
    now_value: str

    def now_iso(self) -> str:
        return self.now_value


def test_append_pipeline_snapshot_accepts_injected_time_provider_for_parity(tmp_path) -> None:
    path = tmp_path / "session.jsonl"
    state = PipelineState(user_input="hello")

    append_pipeline_snapshot(
        "answer",
        state,
        log_path=path,
        time_provider=_FixedSnapshotClock("2026-03-19T00:00:00Z"),
    )

    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["ts"] == "2026-03-19T00:00:00Z"
