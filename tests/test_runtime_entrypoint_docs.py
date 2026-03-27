from __future__ import annotations

from pathlib import Path


DOCS_WITH_RUNTIME_COMMANDS = [
    Path("docs/quickstart.md"),
    Path("docs/ops.md"),
]

LEGACY_RUNTIME_COMMAND = "python src/testbot/sat_chatbot_memory_v2.py"


def test_runtime_docs_do_not_use_legacy_monolith_entrypoint_command() -> None:
    for doc_path in DOCS_WITH_RUNTIME_COMMANDS:
        text = doc_path.read_text()
        assert LEGACY_RUNTIME_COMMAND not in text, f"Legacy runtime command still present in {doc_path}"
