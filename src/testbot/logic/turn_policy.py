"""Deterministic helper logic for turn-policy execution paths.

Ownership:
- Canonical owner for reusable deterministic transforms consumed by
  turn-pipeline/telemetry wiring.
- Legacy compatibility façades should delegate here instead of re-owning logic.
"""

from __future__ import annotations

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


__all__ = ["ambiguity_score", "optional_string"]
