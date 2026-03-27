from __future__ import annotations

from pathlib import Path


DOCS_WITH_RUNTIME_COMMANDS = [
    Path("docs/quickstart.md"),
    Path("docs/ops.md"),
]

LEGACY_RUNTIME_COMMAND = "python src/testbot/sat_chatbot_memory_v2.py"
LEGACY_SOURCE_INGEST_TOGGLE = "SOURCE_INGEST_ENABLED=1"


def test_runtime_docs_do_not_use_legacy_monolith_entrypoint_command() -> None:
    for doc_path in DOCS_WITH_RUNTIME_COMMANDS:
        text = doc_path.read_text()
        assert LEGACY_RUNTIME_COMMAND not in text, f"Legacy runtime command still present in {doc_path}"


def test_runtime_docs_use_cli_source_ingestion_selection_not_env_enable_toggle() -> None:
    for doc_path in DOCS_WITH_RUNTIME_COMMANDS:
        text = doc_path.read_text()
        assert "--source-ingestion" in text, f"Expected CLI source-ingestion selector guidance in {doc_path}"
        assert "--source-ingestion menu" in text, f"Expected menu entry mode guidance in {doc_path}"
        assert "--source-ingestion reference" in text, f"Expected reference entry mode guidance in {doc_path}"
        assert "--source-ingestion freeform" in text, f"Expected freeform entry mode guidance in {doc_path}"
        assert LEGACY_SOURCE_INGEST_TOGGLE not in text, f"Legacy source-ingest env toggle still present in {doc_path}"
