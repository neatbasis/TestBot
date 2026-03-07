from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_markdown_paths.py"
_validator_spec = importlib.util.spec_from_file_location("validate_markdown_paths", _VALIDATOR_PATH)
assert _validator_spec and _validator_spec.loader
validate_markdown_paths = importlib.util.module_from_spec(_validator_spec)
sys.modules[_validator_spec.name] = validate_markdown_paths
_validator_spec.loader.exec_module(validate_markdown_paths)


def test_validate_links_fails_when_canonical_and_legacy_feature_status_coexist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "feature-status.yaml"
    legacy = tmp_path / "feature-status.yml"
    canonical.write_text("meta: {}\n", encoding="utf-8")
    legacy.write_text("meta: {}\n", encoding="utf-8")

    monkeypatch.setattr(validate_markdown_paths, "iter_markdown_files", lambda: [])
    monkeypatch.setattr(validate_markdown_paths, "CANONICAL_FEATURE_STATUS_PATH", canonical)
    monkeypatch.setattr(validate_markdown_paths, "LEGACY_FEATURE_STATUS_PATH", legacy)

    assert validate_markdown_paths.validate_links() == 1


def test_validate_links_passes_when_only_canonical_feature_status_exists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "feature-status.yaml"
    legacy = tmp_path / "feature-status.yml"
    canonical.write_text("meta: {}\n", encoding="utf-8")

    monkeypatch.setattr(validate_markdown_paths, "iter_markdown_files", lambda: [])
    monkeypatch.setattr(validate_markdown_paths, "CANONICAL_FEATURE_STATUS_PATH", canonical)
    monkeypatch.setattr(validate_markdown_paths, "LEGACY_FEATURE_STATUS_PATH", legacy)

    assert validate_markdown_paths.validate_links() == 0
