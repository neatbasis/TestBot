from __future__ import annotations

from testbot.observability.transition_validation import append_transition_validation_log


def transition_validation_failure_message(result: object) -> str:
    failures = ", ".join(getattr(result, "failures", ()))
    stage = getattr(result, "stage", "<unknown>")
    boundary = getattr(result, "boundary", "<unknown>")
    return f"Stage transition validation failed at {stage}.{boundary}: {failures}"


def validate_and_log_transition(result: object) -> None:
    append_transition_validation_log(result)
    if not getattr(result, "passed", False):
        raise AssertionError(transition_validation_failure_message(result))


__all__ = ["transition_validation_failure_message", "validate_and_log_transition"]
