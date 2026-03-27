from __future__ import annotations

from types import SimpleNamespace

from testbot.source_ingestion_entry import (
    apply_freeform_request,
    apply_reference_example,
    apply_source_ingestion_entry,
)


def test_apply_reference_example_sets_known_good_runtime_defaults() -> None:
    runtime: dict[str, object] = {}

    selection = apply_reference_example(runtime=runtime, reference_key="wikipedia_hilbert", selected_via="cli")

    assert selection.mode == "reference"
    assert selection.connector_type == "wikipedia"
    assert selection.reference_key == "wikipedia_hilbert"
    assert runtime["source_ingest_enabled"] is True
    assert runtime["source_connector_type"] == "wikipedia"
    assert runtime["source_wikipedia_topic"] == "Hilbert space"


def test_apply_freeform_request_parses_connector_and_value() -> None:
    runtime: dict[str, object] = {}

    selection = apply_freeform_request(runtime=runtime, request="arxiv:all:'category theory'", selected_via="menu")

    assert selection.mode == "freeform"
    assert selection.connector_type == "arxiv"
    assert selection.freeform_request == "arxiv:all:'category theory'"
    assert runtime["source_ingest_enabled"] is True
    assert runtime["source_connector_type"] == "arxiv"
    assert runtime["source_arxiv_query"] == "all:'category theory'"


def test_apply_source_ingestion_entry_menu_reference_path_is_supported() -> None:
    runtime: dict[str, object] = {}
    prompts = iter(["1", "1"])

    selection = apply_source_ingestion_entry(
        args=SimpleNamespace(source_ingestion="menu"),
        runtime=runtime,
        input_fn=lambda _prompt: next(prompts),
        print_fn=lambda _line: None,
    )

    assert selection.selected_via == "menu"
    assert selection.reference_key == "wikipedia_hilbert"
    assert runtime["source_ingest_enabled"] is True
    assert runtime["source_connector_type"] == "wikipedia"


def test_apply_source_ingestion_entry_freeform_mode_prompts_when_missing_inline_value() -> None:
    runtime: dict[str, object] = {}

    selection = apply_source_ingestion_entry(
        args=SimpleNamespace(source_ingestion="freeform", source_freeform=""),
        runtime=runtime,
        input_fn=lambda _prompt: "wikipedia:Category theory",
        print_fn=lambda _line: None,
    )

    assert selection.mode == "freeform"
    assert selection.connector_type == "wikipedia"
    assert runtime["source_wikipedia_topic"] == "Category theory"


def test_menu_copy_exposes_canonical_entry_modes() -> None:
    runtime: dict[str, object] = {}
    printed: list[str] = []

    selection = apply_source_ingestion_entry(
        args=SimpleNamespace(source_ingestion="menu"),
        runtime=runtime,
        input_fn=lambda _prompt: "4",
        print_fn=lambda line: printed.append(line),
    )

    joined = "\n".join(printed)
    assert "Apply a reference example" in joined
    assert "Start from freeform request" in joined
    assert "Choose a direct connector" in joined
    assert "Keep ingestion disabled" in joined
    assert selection.mode == "off"
