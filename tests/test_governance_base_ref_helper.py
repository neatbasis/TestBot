from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


helper = _load_module("governance_base_ref_for_tests", _SCRIPTS_DIR / "governance_base_ref.py")


def test_resolve_base_ref_uses_canonical_fallback_order() -> None:
    observed: list[str] = []

    def ref_exists(ref: str) -> bool:
        observed.append(ref)
        return ref == "HEAD"

    resolved, notes = helper.resolve_base_ref("origin/main", ref_exists=ref_exists)

    assert resolved == "HEAD"
    assert observed == ["origin/main", helper.EPHEMERAL_ORIGIN_MAIN_REF, "HEAD~1", "HEAD"]
    assert any("falling back to 'HEAD'" in note for note in notes)


def test_resolve_base_ref_returns_canonical_degraded_note_when_unavailable() -> None:
    resolved, notes = helper.resolve_base_ref("origin/main", ref_exists=lambda _ref: False)

    assert resolved is None
    assert notes == [helper.NO_USABLE_BASE_REF_NOTE]


def test_commit_traceability_fail_closed_message_is_shared() -> None:
    failure = helper.commit_traceability_failure(
        requested_base_ref="origin/main",
        effective_base_ref="HEAD~1",
        allow_degraded_commit_traceability=False,
    )

    assert failure is not None
    message, hint = failure
    assert "fail closed" in message
    assert "Requested 'origin/main' but resolved 'HEAD~1'" in hint
    assert "--allow-degraded-commit-traceability" in hint


def test_commit_traceability_degraded_mode_opt_in_is_allowed() -> None:
    failure = helper.commit_traceability_failure(
        requested_base_ref="origin/main",
        effective_base_ref="HEAD~1",
        allow_degraded_commit_traceability=True,
    )

    assert failure is None


def test_commit_traceability_accepts_recovered_origin_main_ref() -> None:
    failure = helper.commit_traceability_failure(
        requested_base_ref="origin/main",
        effective_base_ref=helper.EPHEMERAL_ORIGIN_MAIN_REF,
        allow_degraded_commit_traceability=False,
    )

    assert failure is None
