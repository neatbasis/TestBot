"""Deterministic helper logic for turn-policy execution paths.

Ownership:
- Canonical owner for reusable deterministic transforms consumed by
  turn-pipeline/telemetry wiring.
- Legacy compatibility façades should delegate here instead of re-owning logic.
"""

from __future__ import annotations

from typing import Mapping

from testbot.policy_decision import DecisionClass, DecisionObject, DecisionReasoning
from testbot.pipeline_state import ConfidenceDecision


def optional_string(value: object) -> str | None:
    if value is None:
        return None
    as_string = str(value).strip()
    if not as_string:
        return None
    return as_string


def ambiguity_score(confidence_decision: dict[str, object]) -> float:
    typed_confidence = ConfidenceDecision.from_mapping(confidence_decision)
    scored_candidates = typed_confidence.typed_scored_candidates()
    if len(scored_candidates) < 2:
        return 0.0
    first = scored_candidates[0] if isinstance(scored_candidates[0], dict) else {}
    second = scored_candidates[1] if isinstance(scored_candidates[1], dict) else {}
    first_score = float(first.get("final_score", 0.0) or 0.0)
    second_score = float(second.get("final_score", 0.0) or 0.0)
    if first_score <= 0.0:
        return 1.0
    separation = max(0.0, first_score - second_score) / first_score
    return round(max(0.0, min(1.0, 1.0 - separation)), 4)


def selected_decision_from_confidence(confidence_decision: Mapping[str, object]) -> DecisionObject | None:
    """Project policy-authoritative selected decisions from confidence payloads."""

    allow_override = bool(confidence_decision.get("allow_selected_decision_override", False))
    authority_stage = str(confidence_decision.get("selected_decision_authority_stage") or "").strip().lower()
    if not allow_override or authority_stage != "policy":
        return None

    raw = confidence_decision.get("selected_decision_object")
    if not isinstance(raw, dict):
        return None

    decision_class_value = str(raw.get("decision_class") or "").strip()
    retrieval_branch = str(raw.get("retrieval_branch") or "").strip()
    if not decision_class_value or not retrieval_branch:
        return None
    try:
        decision_class = DecisionClass(decision_class_value)
    except ValueError:
        return None

    reasoning = raw.get("reasoning")
    if not isinstance(reasoning, Mapping):
        reasoning = {}
    normalized_reasoning = DecisionReasoning.from_mapping({str(key): value for key, value in reasoning.items()}).to_dict()
    normalized_reasoning["authority_stage"] = "policy"
    normalized_reasoning["authority_source"] = "confidence_payload"
    return DecisionObject(
        decision_class=decision_class,
        retrieval_branch=retrieval_branch,
        rationale=str(raw.get("rationale") or "selected_decision_policy_override"),
        reasoning=normalized_reasoning,
    )


__all__ = ["ambiguity_score", "optional_string", "selected_decision_from_confidence"]
