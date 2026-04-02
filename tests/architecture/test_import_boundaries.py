from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "testbot"

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

STAGE_MODULES: tuple[str, ...] = (
    "turn_observation.py",
    "candidate_encoding.py",
    "stabilization.py",
    "context_resolution.py",
    "intent_resolution.py",
    "evidence_retrieval.py",
    "policy_decision.py",
    "answer_assembly.py",
    "answer_validate.py",
    "answer_render.py",
    "answer_commit.py",
)

DOMAIN_TYPE_MODULES: tuple[str, ...] = (
    "pipeline_state.py",
    "intent_router.py",
    "answer_policy.py",
    "response_planner.py",
    "stage_transitions.py",
)

INFRA_ADAPTER_IMPORT_PATTERNS: tuple[str, ...] = (
    "testbot.source_connectors",
    "testbot.source_ingest",
    "testbot.sat_chatbot_memory_v2",
    "homeassistant_api",
    "langchain_ollama",
    "elasticsearch",
)

CLIENT_IMPORT_PATTERNS: tuple[str, ...] = (
    "homeassistant_api",
    "langchain_ollama",
    "elasticsearch",
)

E2E_STAGE_COMPOSITION_ALLOWLIST: tuple[Path, ...] = (
    SRC_ROOT / "canonical_turn_orchestrator.py",
    SRC_ROOT / "sat_chatbot_memory_v2.py",
)

CANONICAL_RENDER_FLOW_ALLOWLIST: dict[Path, set[str]] = {
    SRC_ROOT / "sat_chatbot_memory_v2.py": {"run_canonical_answer_stage_flow", "_run_answer_stages_from_supplied_artifacts", "_answer_render"},
    SRC_ROOT / "answer_rendering.py": {"render_answer"},
    SRC_ROOT / "answer_render.py": set(),
}

DEPRECATED_SAT_RUNTIME_EXPORTS: tuple[str, ...] = (
    "run_answer_stage_flow",
    "evaluate_alignment_decision",
)

DEPRECATED_IMPORT_COMPAT_TEST_ALLOWLIST: tuple[Path, ...] = (
    REPO_ROOT / "tests" / "test_answer_stage_flow_delegation.py",
)

SAT_COMPAT_TEST_IMPORT_ALLOWLIST: tuple[Path, ...] = (
    REPO_ROOT / "tests" / "test_answer_contract_constants_compatibility.py",
    REPO_ROOT / "tests" / "test_answer_stage_flow_delegation.py",
    REPO_ROOT / "tests" / "test_answer_stage_runtime_compat_wrappers.py",
    REPO_ROOT / "tests" / "test_canonical_orchestrator_compatibility_exports.py",
    REPO_ROOT / "tests" / "test_context_retrieval_runtime_compat_wrappers.py",
    REPO_ROOT / "tests" / "test_runtime_capability_extraction_compatibility.py",
    REPO_ROOT / "tests" / "test_runtime_capability_ownership_compatibility.py",
    REPO_ROOT / "tests" / "test_runtime_logging_events_compatibility.py",
    REPO_ROOT / "tests" / "test_runtime_modes_compatibility.py",
    REPO_ROOT / "tests" / "test_time_reasoning_compatibility.py",
    REPO_ROOT / "tests" / "test_runtime_transition_validation_compatibility.py",
    REPO_ROOT / "tests" / "test_sat_runtime_compat_facade.py",
    REPO_ROOT / "tests" / "test_session_log_compatibility.py",
    REPO_ROOT / "tests" / "integration" / "ports_contract" / "test_port_contracts_compatibility.py",
    REPO_ROOT / "tests" / "test_turn_service_delegation_compatibility.py",
)

DEPRECATED_EXPORT_SCAN_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
    REPO_ROOT / "scripts",
)

ASK_ADAPTER_IMPORT_ALLOWLIST: tuple[Path, ...] = (
    SRC_ROOT / "adapters" / "ask_gateway.py",
)

ASK_FORBIDDEN_MODULE_PATTERNS: tuple[str, ...] = (
    "ask",
    "ask.config",
)

ASK_LOW_LEVEL_HELPERS: tuple[str, ...] = (
    "AskClient",
    "AskSpec",
    "Answer",
    "Config",
    "normalize_rest_api_url",
)


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def _contains_pattern(import_name: str, pattern: str) -> bool:
    return import_name == pattern or import_name.startswith(f"{pattern}.")


def _imports_sat_compat_facade(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _contains_pattern(alias.name, "testbot.sat_chatbot_memory_v2"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and _contains_pattern(node.module, "testbot.sat_chatbot_memory_v2"):
                return True
            if node.module == "testbot":
                if any(alias.name == "sat_chatbot_memory_v2" for alias in node.names):
                    return True
    return False


def test_stage_modules_do_not_import_infrastructure_adapters_directly() -> None:
    violations: list[str] = []
    for module_name in STAGE_MODULES:
        path = SRC_ROOT / module_name
        imports = _module_imports(path)
        for imported in sorted(imports):
            for pattern in INFRA_ADAPTER_IMPORT_PATTERNS:
                if _contains_pattern(imported, pattern):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {imported}")
    assert not violations, "Stage module import-boundary violations:\n" + "\n".join(violations)


def test_domain_type_modules_do_not_depend_on_es_ollama_or_home_assistant_clients() -> None:
    violations: list[str] = []
    for module_name in DOMAIN_TYPE_MODULES:
        path = SRC_ROOT / module_name
        imports = _module_imports(path)
        for imported in sorted(imports):
            for pattern in CLIENT_IMPORT_PATTERNS:
                if _contains_pattern(imported, pattern):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {imported}")
    assert not violations, "Domain type client-boundary violations:\n" + "\n".join(violations)


def _canonical_stage_order_assignment_paths() -> list[Path]:
    paths: list[Path] = []
    for path in SRC_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "STAGE_ORDER" for target in node.targets):
                continue
            value = node.value
            if not isinstance(value, (ast.Tuple, ast.List)):
                continue
            raw_values: list[str] = []
            for elt in value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    raw_values.append(elt.value)
            if tuple(raw_values) == CANONICAL_STAGE_ORDER:
                paths.append(path)
    return paths


def test_orchestration_is_only_place_composing_end_to_end_stage_order() -> None:
    composition_paths = _canonical_stage_order_assignment_paths()
    disallowed = [path for path in composition_paths if path not in E2E_STAGE_COMPOSITION_ALLOWLIST]
    assert not disallowed, (
        "Canonical full stage-order composition is only allowed in orchestration modules; "
        f"found additional declarations: {[str(path.relative_to(REPO_ROOT)) for path in disallowed]}"
    )


def test_no_raw_input_to_render_shortcuts_outside_canonical_process_flow() -> None:
    violations: list[str] = []
    for path in SRC_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parent_map: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parent_map[child] = parent

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "render_answer":
                continue

            allowed_functions = CANONICAL_RENDER_FLOW_ALLOWLIST.get(path)
            if allowed_functions is None:
                violations.append(f"{path.relative_to(REPO_ROOT)} calls render_answer")
                continue

            enclosing_function = None
            cursor: ast.AST | None = node
            while cursor is not None:
                cursor = parent_map.get(cursor)
                if isinstance(cursor, ast.FunctionDef):
                    enclosing_function = cursor.name
                    break
            if enclosing_function and enclosing_function in allowed_functions:
                continue
            if not allowed_functions and enclosing_function is None:
                continue
            violations.append(
                f"{path.relative_to(REPO_ROOT)} calls render_answer in disallowed scope {enclosing_function!r}"
            )

    assert not violations, "Raw-input-to-render shortcut violations:\n" + "\n".join(violations)


def test_deprecated_sat_runtime_exports_are_only_imported_by_approved_compatibility_tests() -> None:
    violations: list[str] = []
    for scan_root in DEPRECATED_EXPORT_SCAN_ROOTS:
        for path in scan_root.rglob("*.py"):
            if path == SRC_ROOT / "sat_chatbot_memory_v2.py":
                continue
            if path in DEPRECATED_IMPORT_COMPAT_TEST_ALLOWLIST:
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                if node.module != "testbot.sat_chatbot_memory_v2":
                    continue
                imported_names = {alias.name for alias in node.names}
                used_deprecated_names = sorted(imported_names.intersection(DEPRECATED_SAT_RUNTIME_EXPORTS))
                if used_deprecated_names:
                    violations.append(
                        f"{path.relative_to(REPO_ROOT)} imports deprecated symbol(s): {', '.join(used_deprecated_names)}"
                    )

    assert not violations, (
        "Deprecated sat_chatbot_memory_v2 compatibility exports are restricted to approved compatibility tests:\n"
        + "\n".join(violations)
    )


def test_sat_compatibility_facade_imports_are_frozen_to_allowlisted_tests() -> None:
    sat_importing_tests = {
        path
        for path in (REPO_ROOT / "tests").rglob("*.py")
        if _imports_sat_compat_facade(path)
    }

    compatibility_allowlist = set(SAT_COMPAT_TEST_IMPORT_ALLOWLIST)
    unexpected = sorted(path.relative_to(REPO_ROOT) for path in sat_importing_tests - compatibility_allowlist)
    assert not unexpected, (
        "SAT compatibility facade imports are only allowed in explicit compatibility tests:\n"
        + "\n".join(str(path) for path in unexpected)
    )


def test_only_ask_adapter_modules_import_ask_packages() -> None:
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        if path in ASK_ADAPTER_IMPORT_ALLOWLIST:
            continue
        imports = _module_imports(path)
        for imported in sorted(imports):
            for pattern in ASK_FORBIDDEN_MODULE_PATTERNS:
                if _contains_pattern(imported, pattern):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports forbidden dependency {imported}")

    assert not violations, (
        "High-level modules must not import ask internals directly. Route all Ask interactions "
        "through testbot.adapters.ask_gateway.AskGateway:\n" + "\n".join(violations)
    )


def test_high_level_modules_do_not_call_low_level_ask_helpers_directly() -> None:
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        if path in ASK_ADAPTER_IMPORT_ALLOWLIST:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in ASK_LOW_LEVEL_HELPERS:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)} directly calls {node.func.id}() (low-level Ask helper)"
                )
            elif isinstance(node.func, ast.Attribute) and node.func.attr in ASK_LOW_LEVEL_HELPERS:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)} directly calls {node.func.attr}() (low-level Ask helper)"
                )

    assert not violations, (
        "Use AskGateway as the required seam for Ask operations; do not invoke ask/ask.config helper APIs "
        "from high-level modules:\n" + "\n".join(violations)
    )
