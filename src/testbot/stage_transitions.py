from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from testbot.memory_cards import utc_now_iso
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType


FALLBACK_ANSWER = "I don't know from memory."
DENY_ANSWER = "I can't comply with that request."
TRANSITION_VALIDATION_SCHEMA_VERSION = 2

REQUIRED_ALIGNMENT_DIMENSIONS = (
    "factual_grounding_reliability",
    "safety_compliance_strictness",
    "response_utility",
    "cost_latency_budget",
    "provenance_transparency",
)


@dataclass(frozen=True)
class TransitionCheckResult:
    stage: str
    boundary: str
    invariant_refs: tuple[str, ...]
    passed: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "boundary": self.boundary,
            "invariant_refs": list(self.invariant_refs),
            "passed": self.passed,
            "failures": list(self.failures),
        }


def _is_scored_candidate_list(candidates: list[CandidateHit]) -> bool:
    if not isinstance(candidates, list):
        return False
    return all(
        isinstance(c.doc_id, str) and isinstance(c.score, float) and isinstance(c.ts, str) and isinstance(c.card_type, str)
        for c in candidates
    )




def _is_non_trivial_answer(answer: str) -> bool:
    normalized = (answer or "").strip()
    return normalized not in {"", FALLBACK_ANSWER, DENY_ANSWER, "Can you clarify which memory and time window you mean?", "I can disambiguate this with a quick follow-up question.", "I don't have enough reliable memory to answer directly. I can either help you reconstruct the timeline from what you remember, or suggest where to check next for the missing detail."}


def _has_allowed_provenance_types(state: PipelineState) -> bool:
    allowed = {p.value for p in ProvenanceType}
    return all(isinstance(p, ProvenanceType) and p.value in allowed for p in state.provenance_types)


def _follows_approved_fallback_path(state: PipelineState) -> bool:
    answer_mode = state.invariant_decisions.get("answer_mode")
    final_answer = (state.final_answer or "").strip()

    if answer_mode == "dont-know":
        return final_answer == FALLBACK_ANSWER
    if answer_mode in {"clarify", "assist"}:
        return final_answer not in {"", FALLBACK_ANSWER, DENY_ANSWER}
    return False

def _answer_mode_respects_intent(state: PipelineState) -> bool:
    answer_mode = str(state.invariant_decisions.get("answer_mode", ""))
    if answer_mode != "clarify":
        return True

    resolved_intent = (state.resolved_intent or "").strip()
    if resolved_intent == "memory_recall":
        return True

    allow_non_memory_clarify = bool(state.confidence_decision.get("allow_non_memory_clarify", False))
    return allow_non_memory_clarify


def _run_checks(
    *,
    stage: str,
    boundary: str,
    invariant_refs: tuple[str, ...],
    checks: list[tuple[str, Callable[[PipelineState], bool]]],
    state: PipelineState,
) -> TransitionCheckResult:
    failures = tuple(name for name, predicate in checks if not predicate(state))
    return TransitionCheckResult(
        stage=stage,
        boundary=boundary,
        invariant_refs=invariant_refs,
        passed=not failures,
        failures=failures,
    )


def validate_observe_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="observe",
        boundary="pre",
        invariant_refs=("INV-002",),
        checks=[("user_input_required", lambda s: bool((s.user_input or "").strip()))],
        state=state,
    )


def validate_observe_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="observe",
        boundary="post",
        invariant_refs=("INV-002",),
        checks=[("user_input_preserved", lambda s: bool((s.user_input or "").strip()))],
        state=state,
    )


def validate_encode_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="encode",
        boundary="pre",
        invariant_refs=("INV-002",),
        checks=[("user_input_available", lambda s: bool((s.user_input or "").strip()))],
        state=state,
    )


def validate_encode_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="encode",
        boundary="post",
        invariant_refs=("INV-002",),
        checks=[("rewritten_query_available", lambda s: bool((s.rewritten_query or "").strip()))],
        state=state,
    )


def validate_retrieve_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="retrieve",
        boundary="pre",
        invariant_refs=("INV-002",),
        checks=[("rewritten_query_available", lambda s: bool((s.rewritten_query or "").strip()))],
        state=state,
    )


def validate_retrieve_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="retrieve",
        boundary="post",
        invariant_refs=("INV-002",),
        checks=[("retrieval_candidates_shape", lambda s: _is_scored_candidate_list(s.retrieval_candidates))],
        state=state,
    )


def validate_rerank_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="rerank",
        boundary="pre",
        invariant_refs=("INV-002",),
        checks=[("retrieval_candidates_shape", lambda s: _is_scored_candidate_list(s.retrieval_candidates))],
        state=state,
    )


def validate_rerank_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="rerank",
        boundary="post",
        invariant_refs=("INV-002",),
        checks=[
            ("reranked_hits_shape", lambda s: _is_scored_candidate_list(s.reranked_hits)),
            ("confidence_decision_has_flag", lambda s: isinstance(s.confidence_decision.get("context_confident"), bool)),
        ],
        state=state,
    )


def validate_answer_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="answer",
        boundary="pre",
        invariant_refs=("INV-001", "INV-002", "INV-003"),
        checks=[
            ("confidence_decision_has_flag", lambda s: isinstance(s.confidence_decision.get("context_confident"), bool)),
        ],
        state=state,
    )


def validate_answer_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="answer",
        boundary="post",
        invariant_refs=("INV-001", "INV-002", "INV-003"),
        checks=[
            ("invariant_decisions_recorded", lambda s: isinstance(s.invariant_decisions, dict) and bool(s.invariant_decisions)),
            (
                "alignment_decision_recorded",
                lambda s: isinstance(s.alignment_decision, dict)
                and isinstance(s.alignment_decision.get("dimensions"), dict)
                and isinstance(s.alignment_decision.get("final_alignment_decision"), str),
            ),
            (
                "alignment_dimensions_present",
                lambda s: all(
                    isinstance(s.alignment_decision.get("dimensions", {}).get(dim), float)
                    for dim in REQUIRED_ALIGNMENT_DIMENSIONS
                ),
            ),
            (
                "inv_001_contract_enforced",
                lambda s: bool(s.invariant_decisions.get("answer_contract_valid", False))
                or s.invariant_decisions.get("answer_mode") in {"deny", "dont-know", "clarify", "assist"},
            ),
            (
                "inv_003_general_knowledge_contract_enforced",
                lambda s: bool(s.invariant_decisions.get("general_knowledge_contract_valid", True))
                or s.final_answer == FALLBACK_ANSWER,
            ),
            (
                "inv_002_progressive_fallback_enforced",
                lambda s: (
                    s.final_answer == DENY_ANSWER
                    if s.invariant_decisions.get("answer_mode") == "deny"
                    else (
                        _follows_approved_fallback_path(s)
                        if (
                            not s.confidence_decision.get("context_confident", False)
                            or not (s.draft_answer or "").strip()
                            or not s.invariant_decisions.get("answer_contract_valid", False)
                        )
                        else True
                    )
                ),
            ),
            (
                "answer_mode_intent_consistent",
                lambda s: _answer_mode_respects_intent(s),
            ),
            (
                "alignment_decision_consistent",
                lambda s: s.alignment_decision.get("final_alignment_decision") == "deny"
                if s.final_answer == DENY_ANSWER
                else (
                    s.alignment_decision.get("final_alignment_decision") == "fallback"
                    if s.final_answer == FALLBACK_ANSWER
                    else s.alignment_decision.get("final_alignment_decision") == "allow"
                ),
            ),
            (
                "provenance_enum_values_valid",
                lambda s: _has_allowed_provenance_types(s),
            ),
            (
                "provenance_present_for_non_trivial_answers",
                lambda s: (not _is_non_trivial_answer(s.final_answer))
                or (
                    bool(s.claims)
                    and bool(s.provenance_types)
                    and bool((s.basis_statement or "").strip())
                ),
            ),
        ],
        state=state,
    )


def append_transition_validation_log(
    result: TransitionCheckResult,
    *,
    log_path: Path = Path("./logs/session.jsonl"),
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": "stage_transition_validation",
        "schema_version": TRANSITION_VALIDATION_SCHEMA_VERSION,
        **result.to_dict(),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
