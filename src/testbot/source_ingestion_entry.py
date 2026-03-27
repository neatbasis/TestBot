"""Canonical owner for user-facing source-ingestion selection.

Design baseline follows Ask terminal demo patterns:
- visible scenario-style menu
- reference examples as known-good starts
- freeform request path
- explicit direct connector mode
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


DIRECT_CONNECTOR_MODES: frozenset[str] = frozenset({"fixture", "local_markdown", "wikipedia", "arxiv"})


@dataclass(frozen=True)
class SourceIngestionReferenceExample:
    key: str
    label: str
    connector_type: str
    details: str
    runtime_overrides: dict[str, object]


@dataclass(frozen=True)
class SourceIngestionSelection:
    mode: str
    enabled: bool
    connector_type: str
    selected_via: str
    reference_key: str = ""
    freeform_request: str = ""


def _record_selection_metadata(*, runtime: dict[str, object], selection: SourceIngestionSelection) -> None:
    runtime["source_ingest_selection_mode"] = selection.mode
    runtime["source_ingest_selection_source"] = selection.selected_via
    runtime["source_ingest_reference_key"] = selection.reference_key
    runtime["source_ingest_freeform_request"] = selection.freeform_request


def _reference_examples() -> tuple[SourceIngestionReferenceExample, ...]:
    return (
        SourceIngestionReferenceExample(
            key="wikipedia_hilbert",
            label="Wikipedia: Hilbert space",
            connector_type="wikipedia",
            details="Known-good public ontology example for first-run grounding checks.",
            runtime_overrides={
                "source_wikipedia_topic": "Hilbert space",
                "source_wikipedia_language": "en",
                "source_ingest_limit": 1,
            },
        ),
        SourceIngestionReferenceExample(
            key="local_alignment_docs",
            label="Local markdown: docs/alignment-canon",
            connector_type="local_markdown",
            details="Operator-controlled canonical notes for deterministic local runs.",
            runtime_overrides={
                "source_markdown_path": "./docs/alignment-canon",
                "source_ingest_limit": 20,
            },
        ),
        SourceIngestionReferenceExample(
            key="arxiv_category_theory",
            label="arXiv: category theory query",
            connector_type="arxiv",
            details="Known-good research query for controlled source-ingestion smoke checks.",
            runtime_overrides={
                "source_arxiv_query": 'all:"category theory" AND cat:cs.LG',
                "source_ingest_limit": 5,
            },
        ),
    )


REFERENCE_EXAMPLE_KEYS: tuple[str, ...] = tuple(example.key for example in _reference_examples())


def _apply_direct_connector(*, runtime: dict[str, object], connector_type: str, selected_via: str) -> SourceIngestionSelection:
    runtime["source_ingest_enabled"] = True
    runtime["source_connector_type"] = connector_type
    selection = SourceIngestionSelection(
        mode=connector_type,
        enabled=True,
        connector_type=connector_type,
        selected_via=selected_via,
    )
    _record_selection_metadata(runtime=runtime, selection=selection)
    return selection


def apply_reference_example(*, runtime: dict[str, object], reference_key: str, selected_via: str = "reference") -> SourceIngestionSelection:
    examples = {example.key: example for example in _reference_examples()}
    selected = examples.get(reference_key)
    if selected is None:
        raise ValueError(f"Unknown source-ingestion reference key: {reference_key}")

    runtime.update(selected.runtime_overrides)
    selection = _apply_direct_connector(runtime=runtime, connector_type=selected.connector_type, selected_via=selected_via)
    selection = SourceIngestionSelection(
        mode="reference",
        enabled=selection.enabled,
        connector_type=selection.connector_type,
        selected_via=selected_via,
        reference_key=selected.key,
    )
    _record_selection_metadata(runtime=runtime, selection=selection)
    return selection


def apply_freeform_request(*, runtime: dict[str, object], request: str, selected_via: str = "freeform") -> SourceIngestionSelection:
    raw_request = str(request or "").strip()
    if ":" not in raw_request:
        raise ValueError("Freeform ingestion request must use '<connector>:<value>' format.")

    connector, value = (part.strip() for part in raw_request.split(":", 1))
    connector = connector.lower()
    if not value:
        raise ValueError("Freeform ingestion request value must be non-empty.")

    if connector in {"wikipedia", "wiki"}:
        runtime["source_wikipedia_topic"] = value
        runtime.setdefault("source_wikipedia_language", "en")
        selection = _apply_direct_connector(runtime=runtime, connector_type="wikipedia", selected_via=selected_via)
    elif connector == "arxiv":
        runtime["source_arxiv_query"] = value
        selection = _apply_direct_connector(runtime=runtime, connector_type="arxiv", selected_via=selected_via)
    elif connector in {"local_markdown", "markdown"}:
        runtime["source_markdown_path"] = value
        selection = _apply_direct_connector(runtime=runtime, connector_type="local_markdown", selected_via=selected_via)
    elif connector == "fixture":
        runtime["source_fixture_path"] = value
        selection = _apply_direct_connector(runtime=runtime, connector_type="fixture", selected_via=selected_via)
    else:
        raise ValueError(f"Unsupported freeform connector '{connector}'.")

    selection = SourceIngestionSelection(
        mode="freeform",
        enabled=selection.enabled,
        connector_type=selection.connector_type,
        selected_via=selected_via,
        freeform_request=raw_request,
    )
    _record_selection_metadata(runtime=runtime, selection=selection)
    return selection


def run_source_ingestion_entry_menu(
    *,
    runtime: dict[str, object],
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> SourceIngestionSelection:
    print_fn("Source ingestion setup (canonical entry)")
    print_fn("========================================")
    print_fn("Choose how to start source ingestion:")
    print_fn("1. Apply a reference example (known-good onboarding start)")
    print_fn("2. Start from freeform request (<connector>:<value>)")
    print_fn("3. Choose a direct connector")
    print_fn("4. Keep ingestion disabled")
    print_fn("Next: startup will run ingestion once using the selected mode.")

    choice = input_fn("Select source-ingestion entry mode [1-4]: ").strip()

    if choice == "1":
        print_fn("Reference examples:")
        for idx, example in enumerate(_reference_examples(), start=1):
            print_fn(f"{idx}. {example.key} - {example.label}")
        raw_pick = input_fn("Choose reference example [1-3 or key]: ").strip()
        if raw_pick.isdigit():
            selected_idx = int(raw_pick)
            examples = _reference_examples()
            if 1 <= selected_idx <= len(examples):
                raw_pick = examples[selected_idx - 1].key
        return apply_reference_example(runtime=runtime, reference_key=raw_pick, selected_via="menu")

    if choice == "2":
        request = input_fn("Enter freeform request (<connector>:<value>): ").strip()
        return apply_freeform_request(runtime=runtime, request=request, selected_via="menu")

    if choice == "3":
        print_fn("Direct connectors: fixture, local_markdown, wikipedia, arxiv")
        connector = input_fn("Connector name: ").strip().lower()
        if connector not in {"fixture", "local_markdown", "wikipedia", "arxiv"}:
            raise ValueError(f"Unsupported direct connector '{connector}'.")
        return _apply_direct_connector(runtime=runtime, connector_type=connector, selected_via="menu")

    if choice == "4":
        runtime["source_ingest_enabled"] = False
        selection = SourceIngestionSelection(mode="off", enabled=False, connector_type="", selected_via="menu")
        _record_selection_metadata(runtime=runtime, selection=selection)
        return selection

    raise ValueError(f"Unknown source-ingestion menu choice '{choice}'.")


def apply_source_ingestion_entry(
    *,
    args,
    runtime: dict[str, object],
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> SourceIngestionSelection:
    mode = str(getattr(args, "source_ingestion", "env") or "env").strip().lower()
    reference_key_arg = str(getattr(args, "source_reference", REFERENCE_EXAMPLE_KEYS[0]) or "").strip()
    freeform_request_arg = str(getattr(args, "source_freeform", "") or "").strip()

    if mode != "reference" and reference_key_arg and reference_key_arg != REFERENCE_EXAMPLE_KEYS[0]:
        raise ValueError("--source-reference can only be used with --source-ingestion reference.")
    if mode != "freeform" and freeform_request_arg:
        raise ValueError("--source-freeform can only be used with --source-ingestion freeform.")

    if mode == "env":
        selection = SourceIngestionSelection(
            mode="env",
            enabled=bool(runtime.get("source_ingest_enabled", False)),
            connector_type=str(runtime.get("source_connector_type", "")).strip().lower(),
            selected_via="environment",
        )
        _record_selection_metadata(runtime=runtime, selection=selection)
        return selection

    if mode == "off":
        runtime["source_ingest_enabled"] = False
        selection = SourceIngestionSelection(mode="off", enabled=False, connector_type="", selected_via="cli")
        _record_selection_metadata(runtime=runtime, selection=selection)
        return selection

    if mode == "reference":
        reference_key = reference_key_arg or REFERENCE_EXAMPLE_KEYS[0]
        return apply_reference_example(runtime=runtime, reference_key=reference_key, selected_via="cli")

    if mode == "freeform":
        freeform_request = freeform_request_arg
        if not freeform_request:
            freeform_request = input_fn("Enter freeform request (<connector>:<value>): ").strip()
        return apply_freeform_request(runtime=runtime, request=freeform_request, selected_via="cli")

    if mode == "menu":
        return run_source_ingestion_entry_menu(runtime=runtime, input_fn=input_fn, print_fn=print_fn)

    if mode in DIRECT_CONNECTOR_MODES:
        return _apply_direct_connector(runtime=runtime, connector_type=mode, selected_via="cli")

    raise ValueError(f"Unsupported source-ingestion mode '{mode}'.")


__all__ = [
    "REFERENCE_EXAMPLE_KEYS",
    "SourceIngestionReferenceExample",
    "SourceIngestionSelection",
    "apply_freeform_request",
    "apply_reference_example",
    "apply_source_ingestion_entry",
    "run_source_ingestion_entry_menu",
]
