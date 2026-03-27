# Source-ingestion control surface (canonical)

## Purpose

This page is the canonical contract for the source-ingestion seam introduced in #649 and hardened post-merge.

## Ownership split

The seam is intentionally narrow and explicit:

- `testbot.source_ingestion_entry` owns **user-facing selection** (`--source-ingestion`, menu/reference/freeform/direct connector/off).
- `testbot.source_ingestion_startup` owns **one-shot startup execution** (`run_source_ingestion(...)`).
- Deeper runtime/background ingestion lifecycle (`source_ingest_background_*`, pending/dead-letter registries, lifecycle polling/start) is **deferred** and remains outside this seam.

## CLI mode contract

`--source-ingestion` supports:

- `env` → keep deployment/runtime `SOURCE_*` parameters as configured.
- `off` → disable startup ingestion.
- `menu` → prompt for one of `reference` / `freeform` / `direct connector` / `off`.
- `reference` → apply a known-good key via `--source-reference`.
- `freeform` → apply `<connector>:<value>` via `--source-freeform`.
- Direct connector modes: `fixture`, `local_markdown`, `wikipedia`, `arxiv`.

Flag validity rules:

- `--source-reference` is valid only when `--source-ingestion reference` is selected.
- `--source-freeform` is valid only when `--source-ingestion freeform` is selected.
- Invalid combinations must fail fast with a `ValueError` before startup execution.

## Deferred scope (explicit)

Not part of this hardened seam:

- Background ingestion lifecycle extraction.
- Pending/dead-letter orchestration cleanup.
- Broader `runtime_legacy_bridge` migration.
- New connectors or feature expansion.
