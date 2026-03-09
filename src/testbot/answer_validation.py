from __future__ import annotations

from dataclasses import dataclass

from testbot.answer_assembly import AnswerCandidate


@dataclass(frozen=True)
class ValidatedAnswer:
    passed: bool
    failures: list[str]


REQUIRED_ASSEMBLY_KEYS = (
    "decision_class",
    "rendered_class",
    "retrieval_branch",
    "rationale",
    "pending_repair_state",
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


def validate_answer_assembly_boundary(assembly: AnswerCandidate) -> ValidatedAnswer:
    failures: list[str] = []
    as_mapping = assembly.__dict__
    for key in REQUIRED_ASSEMBLY_KEYS:
        if key not in as_mapping:
            failures.append(f"missing_required_field:{key}")

    pending_repair_state = as_mapping.get("pending_repair_state")
    if not isinstance(pending_repair_state, dict):
        failures.append("pending_repair_state_not_dict")
    else:
        if "required" not in pending_repair_state:
            failures.append("pending_repair_state_missing_required")

    if not isinstance(as_mapping.get("resolved_obligations"), list):
        failures.append("resolved_obligations_not_list")
    if not isinstance(as_mapping.get("remaining_obligations"), list):
        failures.append("remaining_obligations_not_list")
    if not isinstance(as_mapping.get("confirmed_user_facts"), list):
        failures.append("confirmed_user_facts_not_list")

    decision_class = str(as_mapping.get("decision_class") or "")
    rendered_class = str(as_mapping.get("rendered_class") or "")
    expected_rendered_class = DECISION_TO_RENDERED_CLASS.get(decision_class)
    if not expected_rendered_class:
        failures.append("decision_class_unknown")
    elif rendered_class != expected_rendered_class:
        failures.append("decision_rendered_class_conflict")

    return ValidatedAnswer(passed=not failures, failures=failures)


# Backward-compatible aliases while canonical naming converges.
AnswerValidationResult = ValidatedAnswer
