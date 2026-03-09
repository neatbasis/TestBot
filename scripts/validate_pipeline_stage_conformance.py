#!/usr/bin/env python3
"""Validate canonical pipeline stage ordering and anti-projection safeguards."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_STAGE_ORDER: tuple[str, ...] = (
    "observe.turn",
    "encode.candidates",
    "stabilize.pre_route",
    "context.resolve",
    "intent.resolve",
    "retrieve.evidence",
    "policy.decide",
    "answer.assemble",
    "answer.validate",
    "answer.render",
    "answer.commit",
)
REQUIRED_INTENT_PRECONDITION_KEYS: tuple[str, ...] = (
    "turn_observation",
    "encoded_candidates",
    "stabilized_turn_state",
)


class ValidationError(RuntimeError):
    """Raised when validation source files are malformed or incomplete."""


def _extract_stages_from_architecture_doc(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    stages: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith(tuple(f"{i}. **`" for i in range(1, 12))):
            continue
        parts = stripped.split("`")
        if len(parts) >= 2:
            stages.append(parts[1])
    return stages


def _extract_stages_from_invariants_table(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if "## Stage transition contracts" not in text:
        raise ValidationError(f"Missing 'Stage transition contracts' section in {path}")
    section = text.split("## Stage transition contracts", maxsplit=1)[1]
    stages: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| `"):
            continue
        stage = stripped.split("`", maxsplit=2)[1]
        if stage == "Stage":
            continue
        stages.append(stage)
    return stages


def _extract_orchestrator_stage_order(path: Path) -> tuple[str, ...]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(module):
        if not isinstance(node, ast.ClassDef) or node.name != "CanonicalTurnOrchestrator":
            continue
        for class_node in node.body:
            value_node: ast.AST | None = None
            if isinstance(class_node, ast.Assign):
                for target in class_node.targets:
                    if isinstance(target, ast.Name) and target.id == "STAGE_ORDER":
                        value_node = class_node.value
                        break
            if isinstance(class_node, ast.AnnAssign) and isinstance(class_node.target, ast.Name):
                if class_node.target.id == "STAGE_ORDER":
                    value_node = class_node.value
            if value_node is None:
                continue
            if not isinstance(value_node, ast.Tuple):
                raise ValidationError("CanonicalTurnOrchestrator.STAGE_ORDER must be a tuple literal")
            return tuple(ast.literal_eval(value_node))
    raise ValidationError(f"Could not find CanonicalTurnOrchestrator.STAGE_ORDER in {path}")


def _extract_intent_precondition_keys(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    observed_keys: set[str] = set()
    for node in ast.walk(module):
        if not isinstance(node, ast.If):
            continue
        if not isinstance(node.test, ast.Compare) or not node.test.comparators:
            continue
        participants: set[str] = set()
        if isinstance(node.test.left, ast.Constant) and isinstance(node.test.left.value, str):
            participants.add(node.test.left.value)
        if isinstance(node.test.left, ast.Name):
            participants.add(node.test.left.id)
        first_comparator = node.test.comparators[0]
        if isinstance(first_comparator, ast.Constant) and isinstance(first_comparator.value, str):
            participants.add(first_comparator.value)
        if isinstance(first_comparator, ast.Name):
            participants.add(first_comparator.id)
        if not {"intent.resolve", "expected_stage"}.issubset(participants):
            continue
        for branch_node in node.body:
            if not isinstance(branch_node, ast.If):
                continue
            test = branch_node.test
            if not isinstance(test, ast.Compare):
                continue
            if not isinstance(test.left, ast.Constant):
                continue
            if not test.comparators:
                continue
            comparator = test.comparators[0]
            if not (
                isinstance(comparator, ast.Attribute)
                and comparator.attr == "artifacts"
            ):
                continue
            if not (
                isinstance(test.ops[0], ast.NotIn)
                and isinstance(test.left.value, str)
            ):
                continue
            observed_keys.add(test.left.value)
    return observed_keys


def validate_pipeline_stage_conformance(
    *,
    architecture_doc: Path = REPO_ROOT / "docs" / "architecture.md",
    canonical_pipeline_doc: Path = REPO_ROOT / "docs" / "architecture" / "canonical-turn-pipeline.md",
    invariants_doc: Path = REPO_ROOT / "docs" / "invariants" / "pipeline.md",
    orchestrator_path: Path = REPO_ROOT / "src" / "testbot" / "canonical_turn_orchestrator.py",
) -> list[str]:
    errors: list[str] = []

    architecture_stages = _extract_stages_from_architecture_doc(architecture_doc)
    if tuple(architecture_stages) != CANONICAL_STAGE_ORDER:
        errors.append(
            "docs/architecture.md stage list must match canonical stage ordering: "
            f"expected {CANONICAL_STAGE_ORDER}, got {tuple(architecture_stages)}"
        )

    invariant_stages = _extract_stages_from_invariants_table(invariants_doc)
    if tuple(invariant_stages) != CANONICAL_STAGE_ORDER:
        errors.append(
            "docs/invariants/pipeline.md stage transition contracts must match canonical stage ordering: "
            f"expected {CANONICAL_STAGE_ORDER}, got {tuple(invariant_stages)}"
        )

    pipeline_text = canonical_pipeline_doc.read_text(encoding="utf-8")
    if "Avoid early lossy projection" not in pipeline_text or "U → I" not in pipeline_text:
        errors.append(
            "docs/architecture/canonical-turn-pipeline.md must preserve the forbidden early projection contract 'U → I'."
        )

    invariants_text = invariants_doc.read_text(encoding="utf-8")
    if "U → I" not in invariants_text and "U -> I" not in invariants_text:
        errors.append("docs/invariants/pipeline.md must explicitly document the forbidden early U -> I projection guard.")

    stage_order = _extract_orchestrator_stage_order(orchestrator_path)
    if stage_order != CANONICAL_STAGE_ORDER:
        errors.append(
            "src/testbot/canonical_turn_orchestrator.py STAGE_ORDER must match canonical stage ordering: "
            f"expected {CANONICAL_STAGE_ORDER}, got {stage_order}"
        )

    observed_keys = _extract_intent_precondition_keys(orchestrator_path)
    missing_keys = [key for key in REQUIRED_INTENT_PRECONDITION_KEYS if key not in observed_keys]
    if missing_keys:
        errors.append(
            "intent.resolve must require pre-intent artifacts to guard against early U -> I projection; "
            f"missing checks for keys: {missing_keys}"
        )

    return errors


def main() -> int:
    errors = validate_pipeline_stage_conformance()
    if errors:
        print("Pipeline stage conformance validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Pipeline stage conformance validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
