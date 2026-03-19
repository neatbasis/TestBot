from __future__ import annotations

from dataclasses import dataclass

from testbot.answer_assembly import AnswerCandidate
from testbot.pipeline_state import ProvenanceType


@dataclass(frozen=True)
class ValidatedAnswer:
    passed: bool
    failures: list[str]
    final_answer: str = ""
    claims: list[str] | None = None
    provenance_types: list[ProvenanceType] | None = None
    used_memory_refs: list[str] | None = None
    used_source_evidence_refs: list[str] | None = None
    source_evidence_attribution: list[dict[str, str]] | None = None
    basis_statement: str = ""
    invariant_decisions: dict[str, object] | None = None
    alignment_decision: dict[str, object] | None = None


REQUIRED_ASSEMBLY_KEYS = (
    "decision_class",
    "rendered_class",
    "retrieval_branch",
    "rationale",
    "pending_repair_state",
    "pending_ingestion_request_id",
    "resolved_obligations",
    "remaining_obligations",
    "confirmed_user_facts",
)


DECISION_TO_RENDERED_CLASS = {
    "answer_from_memory": "answer_from_memory",
    "ask_for_clarification": "ask_for_clarification",
    "continue_repair_reconstruction": "continue_repair_reconstruction",
    "answer_general_knowledge_labeled": "answer_general_knowledge_labeled",
    "pending_lookup_background_ingestion": "pending_lookup_background_ingestion",
}


def validate_answer_assembly_boundary(
    assembly: AnswerCandidate,
    *,
    final_answer: str = "",
    claims: list[str] | None = None,
    provenance_types: list[ProvenanceType] | None = None,
    used_memory_refs: list[str] | None = None,
    used_source_evidence_refs: list[str] | None = None,
    source_evidence_attribution: list[dict[str, str]] | None = None,
    basis_statement: str = "",
    invariant_decisions: dict[str, object] | None = None,
    alignment_decision: dict[str, object] | None = None,
) -> ValidatedAnswer:
    failures: list[str] = []
    for key in REQUIRED_ASSEMBLY_KEYS:
        if not hasattr(assembly, key):
            failures.append(f"missing_required_field:{key}")

    if not isinstance(assembly.pending_repair_state.repair_required_by_policy, bool):
        failures.append("pending_repair_state_invalid_repair_required_by_policy")
    if not isinstance(assembly.pending_repair_state.repair_offered_to_user, bool):
        failures.append("pending_repair_state_invalid_repair_offered_to_user")

    if not isinstance(assembly.resolved_obligations, list):
        failures.append("resolved_obligations_not_list")
    if not isinstance(assembly.remaining_obligations, list):
        failures.append("remaining_obligations_not_list")
    if not isinstance(assembly.confirmed_user_facts, list):
        failures.append("confirmed_user_facts_not_list")

    if not isinstance(assembly.pending_ingestion_request_id, str):
        failures.append("pending_ingestion_request_id_not_str")

    decision_class = str(assembly.decision_class or "")
    rendered_class = str(assembly.rendered_class or "")
    expected_rendered_class = DECISION_TO_RENDERED_CLASS.get(decision_class)
    if not expected_rendered_class:
        failures.append("decision_class_unknown")
    elif rendered_class != expected_rendered_class:
        failures.append("decision_rendered_class_conflict")

    return ValidatedAnswer(
        passed=not failures,
        failures=failures,
        final_answer=final_answer,
        claims=list(claims or []),
        provenance_types=list(provenance_types or []),
        used_memory_refs=list(used_memory_refs or []),
        used_source_evidence_refs=list(used_source_evidence_refs or []),
        source_evidence_attribution=list(source_evidence_attribution or []),
        basis_statement=basis_statement,
        invariant_decisions=dict(invariant_decisions or {}),
        alignment_decision=dict(alignment_decision or {}),
    )


# Backward-compatible aliases while canonical naming converges.
AnswerValidationResult = ValidatedAnswer
