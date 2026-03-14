#!/usr/bin/env python3
"""Validate canonical pipeline stage ordering and ontology-separation safeguards."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
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
PIPELINE_INVARIANT_PATTERN = re.compile(r"\bPINV-\d+\b")
RESPONSE_POLICY_INVARIANT_PATTERN = re.compile(r"\bINV-\d+\b")
DOWNSTREAM_POLICY_CONSEQUENCE_MARKERS: tuple[str, ...] = (
    "downstream answer-policy",
    "downstream response-policy",
    "answer-policy consequence",
    "response-policy consequence",
    "answer-contract consequence",
    "downstream answer contract",
)


class ValidationError(RuntimeError):
    """Raised when validation source files are malformed or incomplete."""


@dataclass(frozen=True)
class PipelineOntologyTableRule:
    section_heading: str | None
    header_first_cells: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class MarkdownTableRow:
    section_heading: str
    row_label: str
    text: str
    line_number: int


PIPELINE_ONTOLOGY_TABLE_RULES: dict[str, tuple[PipelineOntologyTableRule, ...]] = {
    "docs/directives/traceability-matrix.md": (
        PipelineOntologyTableRule(
            section_heading=None,
            header_first_cells=("Canonical stage group", "Phase"),
            description="pipeline stage checkpoint rows",
        ),
    ),
    "docs/invariants/pipeline.md": (
        PipelineOntologyTableRule(
            section_heading="## Stage transition contracts",
            header_first_cells=("Stage",),
            description="stage transition contract rows",
        ),
    ),
}


def _extract_stages_from_canonical_pipeline_doc(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    marker = "## Canonical stage sequence"
    if marker not in text:
        raise ValidationError(f"Missing '{marker}' section in {path}")
    section = text.split(marker, maxsplit=1)[1]

    code_block_match = re.search(r"```(?:text)?\n(.*?)\n```", section, flags=re.DOTALL)
    if not code_block_match:
        raise ValidationError(f"Missing canonical stage-sequence code block in {path}")

    stages: list[str] = []
    for raw_line in code_block_match.group(1).splitlines():
        stripped = raw_line.strip().lstrip("→").strip()
        if not stripped:
            continue
        if "." not in stripped:
            continue
        stages.append(stripped)
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
            if not (isinstance(comparator, ast.Attribute) and comparator.attr == "artifacts"):
                continue
            if not (isinstance(test.ops[0], ast.NotIn) and isinstance(test.left.value, str)):
                continue
            observed_keys.add(test.left.value)
    return observed_keys


def _extract_markdown_table_rows_for_section(path: Path, rule: PipelineOntologyTableRule) -> list[MarkdownTableRow]:
    lines = path.read_text(encoding="utf-8").splitlines()
    section_line_index = 0
    if rule.section_heading is not None:
        section_line_index = None
        for idx, line in enumerate(lines):
            if line.strip() == rule.section_heading:
                section_line_index = idx
                break
        if section_line_index is None:
            raise ValidationError(f"Missing required section '{rule.section_heading}' in {path}")

    rows: list[MarkdownTableRow] = []
    found_header = False
    for idx in range(section_line_index + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") and rule.section_heading is not None:
            break
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if not found_header:
            if cells[0] in rule.header_first_cells:
                found_header = True
            continue
        if set(cells[0]) <= {"-", ":"}:
            continue
        if cells[0] in {"Phase", "Stage", "Pipeline Invariant ID", "Canonical stage group"}:
            continue
        rows.append(
            MarkdownTableRow(
                section_heading=rule.section_heading or "<document-level-table>",
                row_label=cells[0],
                text=" ".join(cells),
                line_number=idx + 1,
            )
        )
    if not found_header:
        raise ValidationError(
            f"Could not find expected table header in {rule.header_first_cells} for ontology rule in {path}"
        )
    return rows


def _allows_mixed_ontology(row_text: str) -> bool:
    lowered = row_text.lower()
    return any(marker in lowered for marker in DOWNSTREAM_POLICY_CONSEQUENCE_MARKERS)


def validate_pipeline_ontology_separation(
    *,
    traceability_doc: Path = REPO_ROOT / "docs" / "directives" / "traceability-matrix.md",
    pipeline_invariants_doc: Path = REPO_ROOT / "docs" / "invariants" / "pipeline.md",
) -> list[str]:
    errors: list[str] = []
    docs = {
        "docs/directives/traceability-matrix.md": traceability_doc,
        "docs/invariants/pipeline.md": pipeline_invariants_doc,
    }

    for doc_key, rules in PIPELINE_ONTOLOGY_TABLE_RULES.items():
        path = docs[doc_key]
        for rule in rules:
            for row in _extract_markdown_table_rows_for_section(path, rule):
                pipeline_refs = PIPELINE_INVARIANT_PATTERN.findall(row.text)
                response_refs = RESPONSE_POLICY_INVARIANT_PATTERN.findall(row.text)
                location = f"{doc_key}:{row.line_number} [{rule.section_heading} | row='{row.row_label}']"

                if not pipeline_refs:
                    if response_refs:
                        errors.append(
                            f"{location} violates ontology split: {rule.description} reference only response-policy IDs "
                            f"{sorted(set(response_refs))}; add at least one PINV-* reference."
                        )
                    else:
                        errors.append(
                            f"{location} violates ontology split: {rule.description} must include at least one "
                            "pipeline invariant reference (PINV-*)."
                        )
                    continue

                if response_refs and not _allows_mixed_ontology(row.text):
                    errors.append(
                        f"{location} mixes PINV/INV references without explicit downstream answer-policy consequences; "
                        f"include one of {DOWNSTREAM_POLICY_CONSEQUENCE_MARKERS}."
                    )

    return errors


def validate_pipeline_stage_conformance(
    *,
    architecture_doc: Path = REPO_ROOT / "docs" / "architecture.md",
    canonical_pipeline_doc: Path = REPO_ROOT / "docs" / "architecture" / "canonical-turn-pipeline.md",
    invariants_doc: Path = REPO_ROOT / "docs" / "invariants" / "pipeline.md",
    traceability_doc: Path = REPO_ROOT / "docs" / "directives" / "traceability-matrix.md",
    orchestrator_path: Path = REPO_ROOT / "src" / "testbot" / "canonical_turn_orchestrator.py",
) -> list[str]:
    errors: list[str] = []

    canonical_stages = _extract_stages_from_canonical_pipeline_doc(canonical_pipeline_doc)
    canonical_stage_order = tuple(canonical_stages)
    if canonical_stage_order != CANONICAL_STAGE_ORDER:
        errors.append(
            "docs/architecture/canonical-turn-pipeline.md canonical stage sequence must match canonical stage ordering: "
            f"expected {CANONICAL_STAGE_ORDER}, got {canonical_stage_order}"
        )

    invariant_stages = _extract_stages_from_invariants_table(invariants_doc)
    if tuple(invariant_stages) != canonical_stage_order:
        errors.append(
            "docs/invariants/pipeline.md stage transition contracts must match canonical stage ordering: "
            f"expected {canonical_stage_order}, got {tuple(invariant_stages)}"
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
    if stage_order != canonical_stage_order:
        errors.append(
            "src/testbot/canonical_turn_orchestrator.py STAGE_ORDER must match canonical stage ordering: "
            f"expected {canonical_stage_order}, got {stage_order}"
        )

    observed_keys = _extract_intent_precondition_keys(orchestrator_path)
    missing_keys = [key for key in REQUIRED_INTENT_PRECONDITION_KEYS if key not in observed_keys]
    if missing_keys:
        errors.append(
            "intent.resolve must require pre-intent artifacts to guard against early U -> I projection; "
            f"missing checks for keys: {missing_keys}"
        )

    errors.extend(
        validate_pipeline_ontology_separation(
            traceability_doc=traceability_doc,
            pipeline_invariants_doc=invariants_doc,
        )
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
