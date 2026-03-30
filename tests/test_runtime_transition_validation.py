from __future__ import annotations

from dataclasses import dataclass

import pytest

from testbot.entrypoints import runtime_transition_validation
from testbot.observability.transition_validation import (
    TRANSITION_VALIDATION_SCHEMA_VERSION,
    build_transition_validation_log_row,
)
from testbot import sat_chatbot_memory_v2 as legacy_runtime


@dataclass(frozen=True)
class _FakeTransitionResult:
    stage: str = "observe.turn"
    boundary: str = "pre"
    passed: bool = True
    failures: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "boundary": self.boundary,
            "invariant_refs": ["PINV-002"],
            "passed": self.passed,
            "failures": list(self.failures),
        }


def test_transition_validation_observability_row_shape_is_canonical() -> None:
    row = build_transition_validation_log_row(
        _FakeTransitionResult(),
        now_iso="2026-03-30T00:00:00+00:00",
    )

    assert row == {
        "ts": "2026-03-30T00:00:00+00:00",
        "event": "stage_transition_validation",
        "schema_version": TRANSITION_VALIDATION_SCHEMA_VERSION,
        "stage": "observe.turn",
        "boundary": "pre",
        "invariant_refs": ["PINV-002"],
        "passed": True,
        "failures": [],
    }


def test_runtime_transition_validation_entrypoint_logs_then_asserts(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}
    result = _FakeTransitionResult(stage="answer.commit", boundary="post", passed=False, failures=("missing", "late"))

    monkeypatch.setattr(
        runtime_transition_validation,
        "append_transition_validation_log",
        lambda candidate: observed.setdefault("result", candidate),
    )

    with pytest.raises(AssertionError, match="answer.commit.post: missing, late"):
        runtime_transition_validation.validate_and_log_transition(result)

    assert observed["result"] is result


def test_legacy_transition_validator_is_compatibility_delegator(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}
    result = _FakeTransitionResult()

    monkeypatch.setattr(
        legacy_runtime,
        "validate_and_log_runtime_transition",
        lambda candidate: observed.setdefault("result", candidate),
    )

    legacy_runtime._validate_and_log_transition(result)
    assert observed["result"] is result
