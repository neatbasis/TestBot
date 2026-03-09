from __future__ import annotations

import testbot.answer_render as answer_render_shim
import testbot.answer_rendering as answer_rendering
import testbot.answer_validate as answer_validate_shim
import testbot.answer_validation as answer_validation


def test_answer_render_shim_re_exports_canonical_symbols() -> None:
    assert answer_render_shim.__all__ == ["RenderedAnswer", "render_answer"]
    assert answer_render_shim.RenderedAnswer is answer_rendering.RenderedAnswer
    assert answer_render_shim.render_answer is answer_rendering.render_answer


def test_answer_validate_shim_re_exports_canonical_symbols() -> None:
    assert answer_validate_shim.__all__ == [
        "REQUIRED_ASSEMBLY_KEYS",
        "DECISION_TO_RENDERED_CLASS",
        "ValidatedAnswer",
        "AnswerValidationResult",
        "validate_answer_assembly_boundary",
    ]
    assert answer_validate_shim.REQUIRED_ASSEMBLY_KEYS is answer_validation.REQUIRED_ASSEMBLY_KEYS
    assert answer_validate_shim.DECISION_TO_RENDERED_CLASS is answer_validation.DECISION_TO_RENDERED_CLASS
    assert answer_validate_shim.ValidatedAnswer is answer_validation.ValidatedAnswer
    assert answer_validate_shim.AnswerValidationResult is answer_validation.AnswerValidationResult
    assert (
        answer_validate_shim.validate_answer_assembly_boundary
        is answer_validation.validate_answer_assembly_boundary
    )
