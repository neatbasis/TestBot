from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from testbot.memory_cards import utc_now_iso
from testbot.pipeline_state import CandidateHit, PipelineState, ProvenanceType, StageArtifact


FALLBACK_ANSWER = "I don't know from memory."
DENY_ANSWER = "I can't comply with that request."
NON_KNOWLEDGE_UNCERTAINTY_ANSWER = (
    "I'm not fully confident in a reliable answer right now. "
    "I can offer a best-effort response and suggest a quick way to verify it."
)
BACKGROUND_INGESTION_PROGRESS_ANSWER = "I'm ingesting external sources in the background now…"
ASSIST_ALTERNATIVES_ANSWER = (
    "I don't have enough reliable memory to answer directly. "
    "I can either help you reconstruct the timeline from what you remember, "
    "or suggest where to check next for the missing detail."
)
TRANSITION_VALIDATION_SCHEMA_VERSION = 4

# One-release migration bridge for downstream telemetry consumers that still
# normalize historical stage transition events keyed by legacy INV-* IDs.
LEGACY_TO_PIPELINE_INVARIANT_REF_MAP: dict[str, str] = {
    "INV-001": "PINV-001",
    "INV-002": "PINV-002",
    "INV-003": "PINV-003",
}

REQUIRED_ALIGNMENT_DIMENSIONS = (
    "factual_grounding_reliability",
    "safety_compliance_strictness",
    "response_utility",
    "cost_latency_budget",
    "provenance_transparency",
)


def migrate_invariant_refs_to_pipeline_namespace(invariant_refs: tuple[str, ...]) -> tuple[str, ...]:
    migrated: list[str] = []
    for invariant_ref in invariant_refs:
        pipeline_ref = LEGACY_TO_PIPELINE_INVARIANT_REF_MAP.get(invariant_ref, invariant_ref)
        if pipeline_ref not in migrated:
            migrated.append(pipeline_ref)
    return tuple(migrated)


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


def _artifact_payload_has_content(payload: object, *, key_fields: tuple[str, ...] = ()) -> bool:
    artifact_dict: dict[str, object] | None = None
    if isinstance(payload, StageArtifact):
        artifact_dict = payload.to_dict()
    elif isinstance(payload, dict):
        artifact_dict = payload
    elif hasattr(payload, "__dict__") and isinstance(payload.__dict__, dict):
        artifact_dict = payload.__dict__

    if artifact_dict is None:
        return False
    if artifact_dict:
        return True
    return any(field in artifact_dict for field in key_fields)


def _artifact_has_non_empty_text_field(payload: object, *, field: str) -> bool:
    if payload is None:
        return False
    value = getattr(payload, field, None)
    return isinstance(value, str) and bool(value.strip())




def _is_non_trivial_answer(answer: str) -> bool:
    normalized = (answer or "").strip()
    return normalized not in {
        "",
        FALLBACK_ANSWER,
        DENY_ANSWER,
        "Can you clarify which memory and time window you mean?",
        "I can disambiguate this with a quick follow-up question.",
        ASSIST_ALTERNATIVES_ANSWER,
    }


def _has_allowed_provenance_types(state: PipelineState) -> bool:
    allowed = {p.value for p in ProvenanceType}
    return all(isinstance(p, ProvenanceType) and p.value in allowed for p in state.provenance_types)


def _has_knowing_mode_provenance_metadata(state: PipelineState) -> bool:
    answer_mode = str(state.invariant_decisions.get("answer_mode", ""))
    if answer_mode in {"deny", "clarify", "dont-know", "assist"}:
        return True

    has_provenance_types = bool(state.provenance_types)
    has_basis_statement = bool((state.basis_statement or "").strip())
    if not (has_provenance_types and has_basis_statement):
        return False

    if ProvenanceType.MEMORY in state.provenance_types:
        return bool(state.used_memory_refs or state.used_source_evidence_refs)
    return True




def _heuristic_only_history_inference(state: PipelineState) -> bool:
    claims = [c.strip() for c in state.claims if c and c.strip()]
    if not claims:
        return False

    allowed_heuristic_prefixes = ("INFERENCE:", "CHAT_HISTORY_OPTIONAL:")
    if not all(claim.startswith(allowed_heuristic_prefixes) for claim in claims):
        return False

    has_heuristic_tag = any(
        "derived_by=heuristic" in claim or "advisory=true" in claim or claim.startswith("CHAT_HISTORY_OPTIONAL:")
        for claim in claims
    )
    if not has_heuristic_tag:
        return False

    return not (state.used_memory_refs or state.used_source_evidence_refs)


def _knowing_mode_not_heuristic_only(state: PipelineState) -> bool:
    answer_mode = str(state.invariant_decisions.get("answer_mode", ""))
    if answer_mode in {"deny", "clarify", "dont-know", "assist"}:
        return True
    if not _is_non_trivial_answer(state.final_answer):
        return True
    return not _heuristic_only_history_inference(state)


def _has_explicit_unknowing_uncertainty_fallback(state: PipelineState) -> bool:
    answer_mode = str(state.invariant_decisions.get("answer_mode", ""))
    if answer_mode != "dont-know":
        return True

    final_answer = (state.final_answer or "").strip()
    if bool(state.confidence_decision.get("background_ingestion_in_progress", False)):
        return final_answer in {FALLBACK_ANSWER, NON_KNOWLEDGE_UNCERTAINTY_ANSWER, BACKGROUND_INGESTION_PROGRESS_ANSWER}
    return final_answer in {FALLBACK_ANSWER, NON_KNOWLEDGE_UNCERTAINTY_ANSWER}


def _classify_canonical_fallback_path(
    *,
    answer_mode: object,
    background_ingestion_in_progress: bool,
    final_answer: str,
) -> str:
    normalized_answer_mode = str(answer_mode or "")
    normalized_final_answer = (final_answer or "").strip()

    if background_ingestion_in_progress and normalized_answer_mode in {"dont-know", "assist"}:
        if normalized_final_answer == BACKGROUND_INGESTION_PROGRESS_ANSWER:
            return "pending_lookup_fallback"

    if normalized_answer_mode == "dont-know":
        if normalized_final_answer in {FALLBACK_ANSWER, NON_KNOWLEDGE_UNCERTAINTY_ANSWER}:
            return "dont_know_non_pending_fallback"

    if normalized_answer_mode in {"clarify", "assist"}:
        if normalized_final_answer not in {"", FALLBACK_ANSWER, DENY_ANSWER}:
            return "assist_or_clarify_non_pending_fallback"

    return "not_fallback"

def _fallback_invariant_outcomes(state: PipelineState) -> dict[str, bool]:
    answer_mode = str(state.invariant_decisions.get("answer_mode", ""))
    fallback_classification = _classify_canonical_fallback_path(
        answer_mode=answer_mode,
        background_ingestion_in_progress=bool(
            state.confidence_decision.get("background_ingestion_in_progress", False)
        ),
        final_answer=(state.final_answer or "").strip(),
    )

    gk_safe_fallback = False
    if fallback_classification == "pending_lookup_fallback":
        gk_safe_fallback = answer_mode in {"dont-know", "assist"}
    elif fallback_classification == "dont_know_non_pending_fallback":
        gk_safe_fallback = answer_mode == "dont-know"
    elif fallback_classification == "assist_or_clarify_non_pending_fallback":
        gk_safe_fallback = answer_mode == "assist" and (state.final_answer or "").strip() == ASSIST_ALTERNATIVES_ANSWER

    if answer_mode == "deny":
        progressive_fallback_ok = state.final_answer == DENY_ANSWER
    else:
        should_apply_progressive_fallback = (
            not state.confidence_decision.get("context_confident", False)
            or not (state.draft_answer or "").strip()
            or not state.invariant_decisions.get("answer_contract_valid", False)
        )
        progressive_fallback_ok = (
            fallback_classification
            in {
                "pending_lookup_fallback",
                "dont_know_non_pending_fallback",
                "assist_or_clarify_non_pending_fallback",
            }
            if should_apply_progressive_fallback
            else True
        )

    return {
        "inv_003_general_knowledge_contract_safe_fallback": gk_safe_fallback,
        "inv_002_progressive_fallback": progressive_fallback_ok,
    }


def _answer_mode_respects_intent(state: PipelineState) -> bool:
    answer_mode = str(state.invariant_decisions.get("answer_mode", ""))
    if answer_mode != "clarify":
        return True

    resolved_intent = (state.resolved_intent or "").strip()
    if resolved_intent == "memory_recall":
        return True

    allow_non_memory_clarify = bool(state.confidence_decision.get("allow_non_memory_clarify", False))
    return allow_non_memory_clarify


def _response_policy_contract_checks() -> list[tuple[str, Callable[[PipelineState], bool]]]:
    return [
        (
            "invariant_decisions_recorded",
            lambda s: hasattr(s.invariant_decisions, "get") and bool(s.invariant_decisions),
        ),
        (
            "inv_001_contract_enforced",
            lambda s: bool(s.invariant_decisions.get("answer_contract_valid", False))
            or s.invariant_decisions.get("answer_mode") in {"deny", "dont-know", "clarify", "assist"},
        ),
        (
            "inv_003_general_knowledge_contract_enforced",
            lambda s: bool(s.invariant_decisions.get("general_knowledge_contract_valid", True))
            or _fallback_invariant_outcomes(s)["inv_003_general_knowledge_contract_safe_fallback"],
        ),
        (
            "inv_002_progressive_fallback_enforced",
            lambda s: _fallback_invariant_outcomes(s)["inv_002_progressive_fallback"],
        ),
    ]


def _alignment_shape_and_decision_checks() -> list[tuple[str, Callable[[PipelineState], bool]]]:
    return [
        (
            "alignment_decision_recorded",
            lambda s: hasattr(s.alignment_decision, "get")
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
            "alignment_decision_consistent",
            lambda s: s.alignment_decision.get("final_alignment_decision") == "deny"
            if s.final_answer == DENY_ANSWER
            else (
                s.alignment_decision.get("final_alignment_decision") == "fallback"
                if s.final_answer == FALLBACK_ANSWER
                else s.alignment_decision.get("final_alignment_decision") == "allow"
            ),
        ),
    ]


def _provenance_requirement_checks() -> list[tuple[str, Callable[[PipelineState], bool]]]:
    return [
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
        (
            "knowing_mode_requires_provenance_metadata",
            lambda s: _has_knowing_mode_provenance_metadata(s),
        ),
        (
            "knowing_mode_disallows_heuristic_only_inference_provenance",
            lambda s: _knowing_mode_not_heuristic_only(s),
        ),
    ]


def _stage_semantics_checks() -> list[tuple[str, Callable[[PipelineState], bool]]]:
    return [
        (
            "answer_mode_intent_consistent",
            lambda s: _answer_mode_respects_intent(s),
        ),
        (
            "unknowing_mode_requires_explicit_uncertainty_fallback",
            lambda s: _has_explicit_unknowing_uncertainty_fallback(s),
        ),
    ]


def _answer_commit_post_checks() -> list[tuple[str, Callable[[PipelineState], bool]]]:
    return [
        *_response_policy_contract_checks(),
        *_alignment_shape_and_decision_checks(),
        *_provenance_requirement_checks(),
        *_stage_semantics_checks(),
    ]


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
    """Deprecated coarse-stage alias; use validate_observe_turn_pre."""
    warnings.warn(
        "validate_observe_pre() is deprecated; use validate_observe_turn_pre().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_observe_turn_pre(state)


def validate_observe_turn_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="observe.turn",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[("user_input_required", lambda s: bool((s.user_input or "").strip()))],
        state=state,
    )


def validate_observe_post(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_observe_turn_post."""
    warnings.warn(
        "validate_observe_post() is deprecated; use validate_observe_turn_post().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_observe_turn_post(state)


def validate_observe_turn_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="observe.turn",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[("user_input_preserved", lambda s: bool((s.user_input or "").strip()))],
        state=state,
    )


def validate_encode_pre(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_encode_candidates_pre."""
    warnings.warn(
        "validate_encode_pre() is deprecated; use validate_encode_candidates_pre().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_encode_candidates_pre(state)


def validate_encode_candidates_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="encode.candidates",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[("user_input_available", lambda s: bool((s.user_input or "").strip()))],
        state=state,
    )


def validate_encode_post(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_encode_candidates_post."""
    warnings.warn(
        "validate_encode_post() is deprecated; use validate_encode_candidates_post().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_encode_candidates_post(state)


def validate_encode_candidates_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="encode.candidates",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[("rewritten_query_available", lambda s: bool((s.rewritten_query or "").strip()))],
        state=state,
    )


def validate_retrieve_pre(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_retrieve_evidence_pre."""
    warnings.warn(
        "validate_retrieve_pre() is deprecated; use validate_retrieve_evidence_pre().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_retrieve_evidence_pre(state)


def validate_retrieve_evidence_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="retrieve.evidence",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[("rewritten_query_available", lambda s: bool((s.rewritten_query or "").strip()))],
        state=state,
    )


def validate_retrieve_post(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_retrieve_evidence_post."""
    warnings.warn(
        "validate_retrieve_post() is deprecated; use validate_retrieve_evidence_post().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_retrieve_evidence_post(state)


def validate_retrieve_evidence_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="retrieve.evidence",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[("retrieval_candidates_shape", lambda s: _is_scored_candidate_list(s.retrieval_candidates))],
        state=state,
    )


def validate_rerank_pre(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_policy_decide_pre."""
    warnings.warn(
        "validate_rerank_pre() is deprecated; use validate_policy_decide_pre().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_policy_decide_pre(state)


def validate_policy_decide_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="policy.decide",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[("retrieval_candidates_shape", lambda s: _is_scored_candidate_list(s.retrieval_candidates))],
        state=state,
    )


def validate_rerank_post(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_policy_decide_post."""
    warnings.warn(
        "validate_rerank_post() is deprecated; use validate_policy_decide_post().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_policy_decide_post(state)


def validate_policy_decide_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="policy.decide",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[
            ("reranked_hits_shape", lambda s: _is_scored_candidate_list(s.reranked_hits)),
            ("confidence_decision_has_flag", lambda s: isinstance(s.confidence_decision.get("context_confident"), bool)),
        ],
        state=state,
    )


def validate_answer_pre(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_answer_assemble_pre."""
    warnings.warn(
        "validate_answer_pre() is deprecated; use validate_answer_assemble_pre().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_answer_assemble_pre(state)


def validate_answer_assemble_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="answer.assemble",
        boundary="pre",
        invariant_refs=("PINV-001", "PINV-002", "PINV-003"),
        checks=[
            ("confidence_decision_has_flag", lambda s: isinstance(s.confidence_decision.get("context_confident"), bool)),
        ],
        state=state,
    )


def validate_answer_post(state: PipelineState) -> TransitionCheckResult:
    """Deprecated coarse-stage alias; use validate_answer_commit_post."""
    warnings.warn(
        "validate_answer_post() is deprecated; use validate_answer_commit_post().",
        DeprecationWarning,
        stacklevel=2,
    )
    return validate_answer_commit_post(state)


def validate_answer_commit_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="answer.commit",
        boundary="post",
        invariant_refs=("PINV-001", "PINV-002", "PINV-003"),
        checks=_answer_commit_post_checks(),
        state=state,
    )


def validate_stabilize_pre_route_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="stabilize.pre_route",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[("rewritten_query_available", lambda s: bool((s.rewritten_query or "").strip()))],
        state=state,
    )


def validate_stabilize_pre_route_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="stabilize.pre_route",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[
            (
                "candidate_facts_recorded",
                lambda s: _artifact_payload_has_content(s.candidate_facts, key_fields=("facts",)),
            )
        ],
        state=state,
    )


def validate_context_resolve_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="context.resolve",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[
            (
                "candidate_facts_available",
                lambda s: _artifact_payload_has_content(s.candidate_facts, key_fields=("facts",)),
            )
        ],
        state=state,
    )


def validate_context_resolve_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="context.resolve",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[
            (
                "resolved_context_recorded",
                lambda s: _artifact_payload_has_content(s.resolved_context, key_fields=("entities", "time_window")),
            )
        ],
        state=state,
    )


def validate_intent_resolve_pre(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="intent.resolve",
        boundary="pre",
        invariant_refs=("PINV-002",),
        checks=[
            (
                "resolved_context_available",
                lambda s: _artifact_payload_has_content(s.resolved_context, key_fields=("entities", "time_window")),
            )
        ],
        state=state,
    )


def validate_intent_resolve_post(state: PipelineState) -> TransitionCheckResult:
    return _run_checks(
        stage="intent.resolve",
        boundary="post",
        invariant_refs=("PINV-002",),
        checks=[("resolved_intent_recorded", lambda s: bool((s.resolved_intent or "").strip()))],
        state=state,
    )


def validate_answer_validate_pre(
    state: PipelineState,
    artifacts: dict[str, object] | None = None,
) -> TransitionCheckResult:
    artifacts = artifacts or {}
    return _run_checks(
        stage="answer.validate",
        boundary="pre",
        invariant_refs=("PINV-001",),
        checks=[
            (
                "draft_answer_present",
                lambda s: _artifact_has_non_empty_text_field(artifacts.get("assembled_answer"), field="draft_answer")
                or _artifact_payload_has_content(
                    artifacts.get("answer_assembly_contract"),
                    key_fields=("decision_class", "rendered_class", "retrieval_branch"),
                )
                or bool((s.draft_answer or "").strip()),
            )
        ],
        state=state,
    )


def validate_answer_validate_post(
    state: PipelineState,
    artifacts: dict[str, object] | None = None,
) -> TransitionCheckResult:
    artifacts = artifacts or {}
    return _run_checks(
        stage="answer.validate",
        boundary="post",
        invariant_refs=("PINV-001",),
        checks=[
            (
                "validation_artifact_present",
                lambda s: bool(s.validation_result.to_dict())
                or _artifact_payload_has_content(artifacts.get("answer_validation_contract"))
                or artifacts.get("validated_answer") is not None,
            )
        ],
        state=state,
    )


def validate_answer_render_pre(
    state: PipelineState,
    artifacts: dict[str, object] | None = None,
) -> TransitionCheckResult:
    artifacts = artifacts or {}
    return _run_checks(
        stage="answer.render",
        boundary="pre",
        invariant_refs=("PINV-001",),
        checks=[
            (
                "final_answer_present",
                lambda s: _artifact_has_non_empty_text_field(artifacts.get("validated_answer"), field="final_answer")
                or _artifact_payload_has_content(artifacts.get("answer_validation_contract"))
                or bool((s.final_answer or "").strip()),
            )
        ],
        state=state,
    )


def validate_answer_render_post(
    state: PipelineState,
    artifacts: dict[str, object] | None = None,
) -> TransitionCheckResult:
    artifacts = artifacts or {}
    return _run_checks(
        stage="answer.render",
        boundary="post",
        invariant_refs=("PINV-001",),
        checks=[
            (
                "final_answer_present",
                lambda s: _artifact_has_non_empty_text_field(artifacts.get("rendered_answer"), field="final_answer")
                or _artifact_payload_has_content(artifacts.get("answer_render_contract"))
                or bool((s.final_answer or "").strip()),
            )
        ],
        state=state,
    )


def validate_answer_commit_pre(
    state: PipelineState,
    artifacts: dict[str, object] | None = None,
) -> TransitionCheckResult:
    artifacts = artifacts or {}
    return _run_checks(
        stage="answer.commit",
        boundary="pre",
        invariant_refs=("PINV-001",),
        checks=[
            (
                "final_answer_present",
                lambda s: _artifact_has_non_empty_text_field(artifacts.get("rendered_answer"), field="final_answer")
                or _artifact_payload_has_content(artifacts.get("answer_render_contract"))
                or bool((s.final_answer or "").strip()),
            )
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
