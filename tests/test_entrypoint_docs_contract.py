from __future__ import annotations

from pathlib import Path


def test_authoritative_docs_keep_cli_entrypoint_canonical_only() -> None:
    quickstart = Path("docs/quickstart.md").read_text()
    ops = Path("docs/ops.md").read_text()

    assert "python -m testbot.entrypoints.cli" in quickstart
    assert "testbot.entrypoints.cli` is canonical" in ops
    assert "testbot.entrypoints.sat_cli" not in quickstart
    assert "testbot.entrypoints.sat_cli" not in ops
