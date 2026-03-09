"""Compatibility shim for answer assembly validation boundaries.

This module exists to provide stable enforcement-point naming for governance
artifacts that reference ``src/testbot/answer_validate.py``.
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
