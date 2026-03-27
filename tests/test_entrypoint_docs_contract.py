from __future__ import annotations

from pathlib import Path


def test_authoritative_docs_keep_cli_entrypoint_canonical_and_sat_cli_non_authoritative() -> None:
    quickstart = Path("docs/quickstart.md").read_text()
    ops = Path("docs/ops.md").read_text()

    assert "python -m testbot.entrypoints.cli" in quickstart
    assert "testbot.entrypoints.cli` is canonical" in ops
    assert "must not be used in new authoritative docs, examples, or automation" in quickstart
