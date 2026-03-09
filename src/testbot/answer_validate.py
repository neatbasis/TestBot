"""Deprecated compatibility shim for answer assembly validation boundaries.

Canonical runtime imports must use :mod:`testbot.answer_validation`.
This shim remains only for external compatibility with legacy references to
``src/testbot/answer_validate.py`` and should not receive new logic.
"""

from __future__ import annotations

from testbot.answer_validation import (  # re-export canonical enforcement points
    DECISION_TO_RENDERED_CLASS,
    REQUIRED_ASSEMBLY_KEYS,
    AnswerValidationResult,
    ValidatedAnswer,
    validate_answer_assembly_boundary,
)

__all__ = [
    "REQUIRED_ASSEMBLY_KEYS",
    "DECISION_TO_RENDERED_CLASS",
    "ValidatedAnswer",
    "AnswerValidationResult",
    "validate_answer_assembly_boundary",
]
