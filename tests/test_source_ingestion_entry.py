from __future__ import annotations

from types import SimpleNamespace

import pytest

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


@pytest.mark.parametrize(
    ("mode", "kwargs", "expected"),
    [
        (
            "env",
            {},
            {
                "mode": "env",
                "enabled": False,
                "connector": "fixture",
                "source": "environment",
            },
        ),
        (
            "off",
            {},
            {
                "mode": "off",
                "enabled": False,
                "connector": "",
                "source": "cli",
            },
        ),
        (
            "reference",
            {"source_reference": "local_alignment_docs"},
            {
                "mode": "reference",
                "enabled": True,
                "connector": "local_markdown",
                "source": "cli",
                "reference": "local_alignment_docs",
            },
        ),
        (
            "freeform",
            {"source_freeform": "wikipedia:Hilbert space"},
            {
                "mode": "freeform",
                "enabled": True,
                "connector": "wikipedia",
                "source": "cli",
                "freeform": "wikipedia:Hilbert space",
            },
        ),
        (
            "wikipedia",
            {},
            {
                "mode": "wikipedia",
                "enabled": True,
                "connector": "wikipedia",
                "source": "cli",
            },
        ),
    ],
)
def test_source_ingestion_modes_emit_expected_runtime_shape(mode: str, kwargs: dict[str, str], expected: dict[str, object]) -> None:
    runtime: dict[str, object] = {
        "source_ingest_enabled": False,
        "source_connector_type": "fixture",
    }
    args_payload = {"source_ingestion": mode, "source_reference": "wikipedia_hilbert", "source_freeform": ""}
    args_payload.update(kwargs)
    args = SimpleNamespace(**args_payload)
    selection = apply_source_ingestion_entry(args=args, runtime=runtime, input_fn=lambda _prompt: "", print_fn=lambda _line: None)

    assert selection.mode == expected["mode"]
    assert selection.enabled is expected["enabled"]
    assert selection.connector_type == expected["connector"]
    assert runtime["source_ingest_selection_source"] == expected["source"]
    if "reference" in expected:
        assert runtime["source_ingest_reference_key"] == expected["reference"]
    if "freeform" in expected:
        assert runtime["source_ingest_freeform_request"] == expected["freeform"]


def test_source_ingestion_reference_flag_is_rejected_for_non_reference_modes() -> None:
    runtime: dict[str, object] = {}
    with pytest.raises(ValueError, match="--source-reference can only be used"):
        apply_source_ingestion_entry(
            args=SimpleNamespace(source_ingestion="wikipedia", source_reference="local_alignment_docs", source_freeform=""),
            runtime=runtime,
        )


def test_source_ingestion_freeform_flag_is_rejected_for_non_freeform_modes() -> None:
    runtime: dict[str, object] = {}
    with pytest.raises(ValueError, match="--source-freeform can only be used"):
        apply_source_ingestion_entry(
            args=SimpleNamespace(source_ingestion="reference", source_reference="wikipedia_hilbert", source_freeform="wikipedia:Hilbert space"),
            runtime=runtime,
        )
