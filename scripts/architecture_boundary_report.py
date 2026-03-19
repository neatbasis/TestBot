#!/usr/bin/env python3
"""Generate a non-blocking architecture boundary report for TestBot modules."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "docs" / "qa" / "architecture-boundaries.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "artifacts" / "architecture-boundary-report.json"


@dataclass(frozen=True)
class ImportEdge:
    importer: str
    imported: str
    importer_area: str | None
    imported_area: str | None
    source_file: str
    line: int


@dataclass(frozen=True)
class Classification:
    status: str
    reason: str
    metadata: dict[str, Any]


class BoundaryConfigError(RuntimeError):
    """Raised when boundary configuration is malformed."""


def _discover_modules(package_root: Path, package_name: str) -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root)
        parts = list(relative.parts)
        if parts[-1] == "__init__.py":
            module = ".".join([package_name, *parts[:-1]])
        else:
            module = ".".join([package_name, *parts])[:-3]
        modules[module] = path
    return modules


def _resolve_from_module(importer: str, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module

    importer_parts = importer.split(".")
    if importer_parts[-1] == "__init__":
        importer_parts = importer_parts[:-1]
    hops_up = max(node.level - 1, 0)
    if hops_up > len(importer_parts) - 1:
        return None
    base_parts = importer_parts[:-hops_up] if hops_up else importer_parts
    if node.module:
        return ".".join([*base_parts, node.module])
    return ".".join(base_parts)


def _expand_import_targets(base_module: str | None, alias_name: str, known_modules: set[str]) -> str | None:
    if base_module is None:
        return None
    if base_module == "testbot" and f"testbot.{alias_name}" in known_modules:
        return f"testbot.{alias_name}"
    candidate = f"{base_module}.{alias_name}"
    if candidate in known_modules:
        return candidate
    return base_module


def _extract_internal_import_edges(
    modules: dict[str, Path],
    package_name: str,
) -> list[tuple[str, str, str, int]]:
    known_modules = set(modules)
    edges: list[tuple[str, str, str, int]] = []

    for module_name, path in sorted(modules.items()):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name
                    if target == package_name or target.startswith(f"{package_name}."):
                        edges.append((module_name, target, str(path.relative_to(REPO_ROOT)), node.lineno))
            elif isinstance(node, ast.ImportFrom):
                base_module = _resolve_from_module(module_name, node)
                if base_module is None:
                    continue
                if not (base_module == package_name or base_module.startswith(f"{package_name}.")):
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        target = base_module
                    else:
                        target = _expand_import_targets(base_module, alias.name, known_modules)
                        if target is None:
                            continue
                    if target == module_name:
                        continue
                    edges.append((module_name, target, str(path.relative_to(REPO_ROOT)), node.lineno))

    # Deduplicate deterministically.
    return sorted(set(edges), key=lambda item: (item[0], item[1], item[2], item[3]))


def _match_any(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _area_for_module(module: str, areas: list[dict[str, Any]]) -> str | None:
    for area in areas:
        patterns = area.get("module_globs", [])
        if _match_any(module, patterns):
            return area["name"]
    return None


def _allowed_for_area(importer_area: str, imported_area: str, areas_by_name: dict[str, dict[str, Any]]) -> bool:
    area = areas_by_name[importer_area]
    allowed = set(area.get("allowed_dependencies", []))
    return imported_area in allowed


def _is_public_surface(imported_module: str, imported_area: str, areas_by_name: dict[str, dict[str, Any]]) -> bool:
    area = areas_by_name[imported_area]
    surface = area.get("public_surface", {})
    public_modules: list[str] = surface.get("modules", [])
    public_prefixes: list[str] = surface.get("module_prefixes", [])

    if imported_module in public_modules:
        return True
    return any(imported_module == prefix or imported_module.startswith(f"{prefix}.") for prefix in public_prefixes)


def _classify_edge(
    edge: ImportEdge,
    *,
    areas_by_name: dict[str, dict[str, Any]],
    temporary_exceptions: list[dict[str, Any]],
    deprecated_patterns: list[str],
) -> Classification:
    if _match_any(edge.importer, deprecated_patterns) or _match_any(edge.imported, deprecated_patterns):
        return Classification(
            status="deprecated_compatibility",
            reason="deprecated_module_compatibility_path",
            metadata={},
        )

    if edge.importer_area is None or edge.imported_area is None:
        return Classification(status="allowed", reason="module_outside_governed_areas", metadata={})

    for exception in temporary_exceptions:
        if fnmatch.fnmatch(edge.importer, exception["importer"]) and fnmatch.fnmatch(edge.imported, exception["imported"]):
            return Classification(
                status="temporary_exception",
                reason="explicit_temporary_exception",
                metadata={
                    "issue": exception.get("issue"),
                    "expires_on": exception.get("expires_on"),
                    "notes": exception.get("notes"),
                },
            )

    if edge.importer_area == edge.imported_area:
        return Classification(status="allowed", reason="same_area_dependency", metadata={})

    if not _allowed_for_area(edge.importer_area, edge.imported_area, areas_by_name):
        return Classification(
            status="violation",
            reason="forbidden_dependency_direction",
            metadata={
                "allowed_dependencies": areas_by_name[edge.importer_area].get("allowed_dependencies", []),
            },
        )

    if not _is_public_surface(edge.imported, edge.imported_area, areas_by_name):
        return Classification(
            status="violation",
            reason="private_surface_import",
            metadata={
                "expected_public_surface": areas_by_name[edge.imported_area].get("public_surface", {}),
            },
        )

    return Classification(status="allowed", reason="allowed_dependency", metadata={})


def generate_architecture_boundary_report(config: dict[str, Any]) -> dict[str, Any]:
    package_name = config.get("package_name", "testbot")
    package_root = REPO_ROOT / config.get("package_root", "src/testbot")
    areas: list[dict[str, Any]] = config["areas"]
    areas_by_name = {area["name"]: area for area in areas}

    if len(areas_by_name) != len(areas):
        raise BoundaryConfigError("Area names must be unique in architecture boundary config.")

    modules = _discover_modules(package_root, package_name)
    module_names = sorted(modules)
    edges = _extract_internal_import_edges(modules, package_name)

    temporary_exceptions = config.get("temporary_exceptions", [])
    deprecated_patterns = config.get("deprecated_compatibility", {}).get("module_globs", [])

    findings: list[dict[str, Any]] = []
    for importer, imported, source_file, line in edges:
        edge = ImportEdge(
            importer=importer,
            imported=imported,
            importer_area=_area_for_module(importer, areas),
            imported_area=_area_for_module(imported, areas),
            source_file=source_file,
            line=line,
        )
        classification = _classify_edge(
            edge,
            areas_by_name=areas_by_name,
            temporary_exceptions=temporary_exceptions,
            deprecated_patterns=deprecated_patterns,
        )
        findings.append(
            {
                "importer": edge.importer,
                "imported": edge.imported,
                "importer_area": edge.importer_area,
                "imported_area": edge.imported_area,
                "classification": classification.status,
                "reason": classification.reason,
                "source_file": edge.source_file,
                "line": edge.line,
                "metadata": classification.metadata,
            }
        )

    counts_by_classification = {
        key: sum(1 for finding in findings if finding["classification"] == key)
        for key in ("violation", "temporary_exception", "deprecated_compatibility", "allowed")
    }

    area_coverage = []
    for area in areas:
        owned_modules = [name for name in module_names if _match_any(name, area.get("module_globs", []))]
        area_coverage.append(
            {
                "name": area["name"],
                "description": area.get("description", ""),
                "module_count": len(owned_modules),
                "sample_modules": owned_modules[:10],
            }
        )

    return {
        "schema_version": "1",
        "config_version": config.get("version", 1),
        "package_name": package_name,
        "package_root": str(package_root.relative_to(REPO_ROOT)),
        "areas": area_coverage,
        "summary": {
            "module_count": len(module_names),
            "import_edge_count": len(edges),
            "counts_by_classification": counts_by_classification,
        },
        "findings": findings,
    }


def _load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    required_top_keys = {"version", "areas"}
    missing = required_top_keys - set(config)
    if missing:
        raise BoundaryConfigError(f"Missing required config keys: {sorted(missing)}")
    return config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to architecture boundaries config JSON (default: {DEFAULT_CONFIG_PATH.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=(
            "Path to write machine-readable JSON report "
            f"(default: {DEFAULT_OUTPUT_PATH.relative_to(REPO_ROOT)})"
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = _load_config(args.config)
    report = generate_architecture_boundary_report(config)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.pretty:
        serialized = json.dumps(report, indent=2, sort_keys=True)
    else:
        serialized = json.dumps(report, sort_keys=True)
    args.output.write_text(f"{serialized}\n", encoding="utf-8")

    summary = report["summary"]["counts_by_classification"]
    print(
        "Architecture boundary report generated "
        f"({report['summary']['import_edge_count']} edges: "
        f"{summary['violation']} violations, "
        f"{summary['temporary_exception']} temporary exceptions, "
        f"{summary['deprecated_compatibility']} deprecated compatibility, "
        f"{summary['allowed']} allowed)."
    )
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
