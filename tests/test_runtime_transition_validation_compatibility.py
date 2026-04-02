from __future__ import annotations

from dataclasses import dataclass

import pytest

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
