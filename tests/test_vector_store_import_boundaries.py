from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "testbot"


DISALLOWED_MODULES = {
    "stabilization.py",
    "memory_cards.py",
    "promotion_policy.py",
    "sat_chatbot_memory_v2.py",
    "application/services/turn_service.py",
    "application/services/canonical_turn_runtime.py",
}

ALLOWED_DIRECT_IMPORTS = {
    "adapters/memory_store_factory.py",
    "rerank.py",
    "source_ingest.py",
}


def _has_direct_vector_store_import(text: str) -> bool:
    return "from testbot.vector_store" in text or "import testbot.vector_store" in text


def test_non_adapter_layers_do_not_directly_import_vector_store() -> None:
    offenders: list[str] = []
    for relative_path in DISALLOWED_MODULES:
        module = SRC_ROOT / relative_path
        if _has_direct_vector_store_import(module.read_text()):
            offenders.append(relative_path)

    assert offenders == []


def test_direct_vector_store_imports_are_limited_to_allowlisted_modules() -> None:
    direct_import_modules: set[str] = set()
    for py_file in SRC_ROOT.rglob("*.py"):
        relative = py_file.relative_to(SRC_ROOT).as_posix()
        if _has_direct_vector_store_import(py_file.read_text()):
            direct_import_modules.add(relative)

    assert direct_import_modules == ALLOWED_DIRECT_IMPORTS
