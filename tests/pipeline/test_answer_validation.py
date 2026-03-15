from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class AnswerCandidate:
    decision_class: str
    answer_class: str
    answer_text: str
    evidence_bindings: list[dict[str, str]]
    hazard_detected: bool = False


@dataclass(frozen=True)
class ValidationResult:
    grounding_sufficient: bool
    provenance_contract_met: bool
    decision_answer_class_aligned: bool

    @property
    def valid(self) -> bool:
        return self.grounding_sufficient and self.provenance_contract_met and self.decision_answer_class_aligned


def answer_assemble(
    *,
    decision_class: str,
    answer_class: str,
    answer_text: str,
    evidence_bindings: list[dict[str, str]] | None = None,
    hazard_detected: bool = False,
) -> AnswerCandidate:
    return AnswerCandidate(
        decision_class=decision_class,
        answer_class=answer_class,
        answer_text=answer_text,
        evidence_bindings=list(evidence_bindings or []),
        hazard_detected=hazard_detected,
    )


def answer_validate(candidate: AnswerCandidate) -> ValidationResult:
    grounding_sufficient = not (
        candidate.decision_class == "ANSWER_FROM_MEMORY"
        and not candidate.evidence_bindings
    )

    provenance_contract_met = all(
        bool(binding.get("provenance_id", "").strip()) for binding in candidate.evidence_bindings
    )

    if candidate.hazard_detected:
        decision_answer_class_aligned = (
            candidate.decision_class == "HAZARD_INTERRUPT"
            and candidate.answer_class == "SAFETY_INTERRUPT"
        )
    else:
        decision_answer_class_aligned = (
            candidate.decision_class != "HAZARD_INTERRUPT"
            and candidate.answer_class != "SAFETY_INTERRUPT"
        )

    return ValidationResult(
        grounding_sufficient=grounding_sufficient,
        provenance_contract_met=provenance_contract_met,
        decision_answer_class_aligned=decision_answer_class_aligned,
    )


def answer_render(candidate: AnswerCandidate, validation: ValidationResult) -> str:
    if not validation.valid:
        return "Stand by."
    return f"NORMAL_RESPONSE::{candidate.answer_text}"


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (
            answer_assemble(
                decision_class="ANSWER_FROM_MEMORY",
                answer_class="STANDARD_RESPONSE",
                answer_text="You said your favorite color is blue.",
                evidence_bindings=[{"claim_id": "c1", "provenance_id": "mem-1"}],
            ),
            True,
        ),
        (
            answer_assemble(
                decision_class="ANSWER_FROM_MEMORY",
                answer_class="STANDARD_RESPONSE",
                answer_text="You said your favorite color is blue.",
                evidence_bindings=[],
            ),
            False,
        ),
    ],
)
def test_grounding_sufficient_requires_bindings_for_answer_from_memory(
    candidate: AnswerCandidate,
    expected: bool,
) -> None:
    result = answer_validate(candidate)

    assert result.grounding_sufficient is expected


@pytest.mark.parametrize(
    ("bindings", "expected"),
    [
        ([{"claim_id": "c1", "provenance_id": "mem-1"}], True),
        ([{"claim_id": "c1", "provenance_id": ""}], False),
        ([{"claim_id": "c1"}], False),
    ],
)
def test_provenance_contract_requires_provenance_id_on_every_binding(
    bindings: list[dict[str, str]],
    expected: bool,
) -> None:
    candidate = answer_assemble(
        decision_class="ANSWER_GENERAL",
        answer_class="STANDARD_RESPONSE",
        answer_text="General answer.",
        evidence_bindings=bindings,
    )

    result = answer_validate(candidate)

    assert result.provenance_contract_met is expected


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (
            answer_assemble(
                decision_class="HAZARD_INTERRUPT",
                answer_class="SAFETY_INTERRUPT",
                answer_text="Stop and move to safety.",
                evidence_bindings=[{"claim_id": "c1", "provenance_id": "policy-1"}],
                hazard_detected=True,
            ),
            True,
        ),
        (
            answer_assemble(
                decision_class="ANSWER_FROM_MEMORY",
                answer_class="STANDARD_RESPONSE",
                answer_text="Normal answer.",
                evidence_bindings=[{"claim_id": "c1", "provenance_id": "mem-1"}],
                hazard_detected=False,
            ),
            True,
        ),
        (
            answer_assemble(
                decision_class="ANSWER_FROM_MEMORY",
                answer_class="STANDARD_RESPONSE",
                answer_text="Should have been interrupt.",
                evidence_bindings=[{"claim_id": "c1", "provenance_id": "mem-1"}],
                hazard_detected=True,
            ),
            False,
        ),
        (
            answer_assemble(
                decision_class="HAZARD_INTERRUPT",
                answer_class="SAFETY_INTERRUPT",
                answer_text="Unexpected interrupt.",
                evidence_bindings=[{"claim_id": "c1", "provenance_id": "policy-1"}],
                hazard_detected=False,
            ),
            False,
        ),
    ],
)
def test_decision_answer_class_aligned_enforces_hazard_alignment_rules(
    candidate: AnswerCandidate,
    expected: bool,
) -> None:
    result = answer_validate(candidate)

    assert result.decision_answer_class_aligned is expected


def test_integration_invalid_candidate_never_renders_normal_response_output() -> None:
    invalid_candidate = answer_assemble(
        decision_class="ANSWER_FROM_MEMORY",
        answer_class="STANDARD_RESPONSE",
        answer_text="I remember this from memory.",
        evidence_bindings=[{"claim_id": "c1", "provenance_id": ""}],
    )

    invalid_validation = answer_validate(invalid_candidate)
    invalid_render = answer_render(invalid_candidate, invalid_validation)

    assert invalid_validation.valid is False
    assert invalid_render == "Stand by."
    assert "NORMAL_RESPONSE::" not in invalid_render

    valid_candidate = answer_assemble(
        decision_class="ANSWER_FROM_MEMORY",
        answer_class="STANDARD_RESPONSE",
        answer_text="I remember this from memory.",
        evidence_bindings=[{"claim_id": "c1", "provenance_id": "mem-1"}],
    )

    valid_validation = answer_validate(valid_candidate)
    valid_render = answer_render(valid_candidate, valid_validation)

    assert valid_validation.valid is True
    assert valid_render.startswith("NORMAL_RESPONSE::")
