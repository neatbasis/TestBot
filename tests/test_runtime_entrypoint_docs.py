from __future__ import annotations

from pathlib import Path


DOCS_WITH_RUNTIME_COMMANDS = [
    Path("docs/quickstart.md"),
    Path("docs/ops.md"),
]
SOURCE_INGESTION_ARCH_DOC = Path("docs/architecture/source-ingestion-control-surface.md")

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


def test_quickstart_presents_menu_onboarding_before_direct_connector_examples() -> None:
    text = Path("docs/quickstart.md").read_text()
    assert text.index("--source-ingestion menu") < text.index("--source-ingestion local_markdown")


def test_runtime_docs_reference_canonical_source_ingestion_control_surface_doc() -> None:
    arch_doc_rel = "docs/architecture/source-ingestion-control-surface.md"
    assert SOURCE_INGESTION_ARCH_DOC.exists()

    quickstart_text = Path("docs/quickstart.md").read_text()
    ops_text = Path("docs/ops.md").read_text()
    assert arch_doc_rel in quickstart_text
    assert arch_doc_rel in ops_text


def test_source_ingestion_architecture_doc_documents_owner_split_and_deferred_scope() -> None:
    text = SOURCE_INGESTION_ARCH_DOC.read_text()
    assert "testbot.source_ingestion_entry" in text
    assert "testbot.source_ingestion_startup" in text
    assert "deferred" in text
