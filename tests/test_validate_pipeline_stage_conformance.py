from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_pipeline_stage_conformance.py"
_validator_spec = importlib.util.spec_from_file_location("validate_pipeline_stage_conformance", _VALIDATOR_PATH)
assert _validator_spec and _validator_spec.loader
validator = importlib.util.module_from_spec(_validator_spec)
sys.modules[_validator_spec.name] = validator
_validator_spec.loader.exec_module(validator)


def test_validate_pipeline_stage_conformance_passes_current_repository_contract() -> None:
    assert validator.validate_pipeline_stage_conformance() == []


def test_validate_pipeline_stage_conformance_accepts_overview_only_architecture_doc(tmp_path: Path) -> None:
    architecture_doc = tmp_path / "architecture.md"
    architecture_doc.write_text(
        "\n".join(
            [
                "# Architecture",
                "## Pipeline overview",
                "This document intentionally links to canonical pipeline details.",
                "See docs/architecture/canonical-turn-pipeline.md for stage ordering.",
            ]
        ),
        encoding="utf-8",
    )

    errors = validator.validate_pipeline_stage_conformance(architecture_doc=architecture_doc)

    assert not any("docs/architecture.md" in error for error in errors)


def test_validate_pipeline_stage_conformance_detects_canonical_pipeline_stage_order_drift(tmp_path: Path) -> None:
    canonical_pipeline_doc = tmp_path / "canonical-turn-pipeline.md"
    canonical_pipeline_doc.write_text(
        "\n".join(
            [
                "# Canonical Turn Pipeline",
                "## Canonical stage sequence",
                "```text",
                "observe.turn",
                "→ intent.resolve",
                "```",
                "Avoid early lossy projection",
                "U → I",
            ]
        ),
        encoding="utf-8",
    )

    errors = validator.validate_pipeline_stage_conformance(canonical_pipeline_doc=canonical_pipeline_doc)

    assert any("canonical-turn-pipeline.md canonical stage sequence" in error for error in errors)


def test_validate_pipeline_stage_conformance_detects_missing_u_to_i_guard_in_invariants(tmp_path: Path) -> None:
    invariants_doc = tmp_path / "invariants.md"
    invariants_doc.write_text(
        "\n".join(
            [
                "## Stage transition contracts",
                "| Stage | Preconditions | Postconditions | Invariant linkage |",
                "|---|---|---|---|",
                *[
                    f"| `{stage}` | pre | post | inv |"
                    for stage in validator.CANONICAL_STAGE_ORDER
                ],
            ]
        ),
        encoding="utf-8",
    )

    errors = validator.validate_pipeline_stage_conformance(invariants_doc=invariants_doc)

    assert "forbidden early U -> I projection guard" in "\n".join(errors)


def test_validate_pipeline_ontology_separation_fails_when_pipeline_semantics_use_only_inv_ids(tmp_path: Path) -> None:
    traceability_doc = tmp_path / "traceability-matrix.md"
    traceability_doc.write_text(
        "\n".join(
            [
                "## Canonical stage checkpoints (ISSUE-0013)",
                "| Phase | Stage boundary | Runtime implementation anchors | BDD scenario coverage | Gate commands | Runtime telemetry evidence | Exit criteria + invariant linkage |",
                "|---|---|---|---|---|---|---|",
                "| **Foundation** | `observe.turn` → `encode.candidates` | impl | bdd | gate | telemetry | Stage semantics described here with **INV-002** only. |",
            ]
        ),
        encoding="utf-8",
    )
    pipeline_doc = tmp_path / "pipeline.md"
    pipeline_doc.write_text(
        "\n".join(
            [
                "## Stage transition contracts",
                "| Stage | Preconditions | Postconditions | Invariant linkage |",
                "|---|---|---|---|",
                "| `observe.turn` | pre | post | `PINV-002` |",
            ]
        ),
        encoding="utf-8",
    )

    errors = validator.validate_pipeline_ontology_separation(
        traceability_doc=traceability_doc,
        pipeline_invariants_doc=pipeline_doc,
    )

    assert any("reference only response-policy IDs" in error for error in errors)


def test_validate_pipeline_ontology_separation_passes_with_pipeline_specific_linkage(tmp_path: Path) -> None:
    traceability_doc = tmp_path / "traceability-matrix.md"
    traceability_doc.write_text(
        "\n".join(
            [
                "## Canonical stage checkpoints (ISSUE-0013)",
                "| Phase | Stage boundary | Runtime implementation anchors | BDD scenario coverage | Gate commands | Runtime telemetry evidence | Exit criteria + invariant linkage |",
                "|---|---|---|---|---|---|---|",
                "| **Foundation** | `observe.turn` → `encode.candidates` | impl | bdd | gate | telemetry | Stage semantics described here with **PINV-001** and **PINV-002**. |",
            ]
        ),
        encoding="utf-8",
    )
    pipeline_doc = tmp_path / "pipeline.md"
    pipeline_doc.write_text(
        "\n".join(
            [
                "## Stage transition contracts",
                "| Stage | Preconditions | Postconditions | Invariant linkage |",
                "|---|---|---|---|",
                "| `observe.turn` | pre | post | `PINV-002` |",
            ]
        ),
        encoding="utf-8",
    )

    assert (
        validator.validate_pipeline_ontology_separation(
            traceability_doc=traceability_doc,
            pipeline_invariants_doc=pipeline_doc,
        )
        == []
    )


def test_validate_pipeline_ontology_separation_allows_mixed_when_downstream_consequence_is_explicit(tmp_path: Path) -> None:
    traceability_doc = tmp_path / "traceability-matrix.md"
    traceability_doc.write_text(
        "\n".join(
            [
                "## Canonical stage checkpoints (ISSUE-0013)",
                "| Phase | Stage boundary | Runtime implementation anchors | BDD scenario coverage | Gate commands | Runtime telemetry evidence | Exit criteria + invariant linkage |",
                "|---|---|---|---|---|---|---|",
                "| **Decisioning** | `intent.resolve` → `retrieve.evidence` | impl | bdd | gate | telemetry | Pipeline semantics enforced by **PINV-003** and downstream answer-policy consequence guarded by **INV-003**. |",
            ]
        ),
        encoding="utf-8",
    )
    pipeline_doc = tmp_path / "pipeline.md"
    pipeline_doc.write_text(
        "\n".join(
            [
                "## Stage transition contracts",
                "| Stage | Preconditions | Postconditions | Invariant linkage |",
                "|---|---|---|---|",
                "| `observe.turn` | pre | post | `PINV-002` |",
            ]
        ),
        encoding="utf-8",
    )

    assert (
        validator.validate_pipeline_ontology_separation(
            traceability_doc=traceability_doc,
            pipeline_invariants_doc=pipeline_doc,
        )
        == []
    )


def test_main_returns_failure_when_conformance_violations_detected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        validator,
        "validate_pipeline_stage_conformance",
        lambda: ["bad stage order", "missing guard"],
    )

    exit_code = validator.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Pipeline stage conformance validation failed" in output
