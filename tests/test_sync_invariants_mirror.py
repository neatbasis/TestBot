from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SYNC_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_invariants_mirror.py"
_sync_spec = importlib.util.spec_from_file_location("sync_invariants_mirror", _SYNC_PATH)
assert _sync_spec and _sync_spec.loader
sync_mod = importlib.util.module_from_spec(_sync_spec)
sys.modules[_sync_spec.name] = sync_mod
_sync_spec.loader.exec_module(sync_mod)


def test_sync_scope_targets_answer_policy_canonical_source() -> None:
    assert sync_mod.CANONICAL_PATH == Path("docs/invariants/answer-policy.md")


def test_extract_synced_block_returns_scoped_block_content() -> None:
    text = """header\n<!-- BEGIN_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->\n\n## Response-policy invariants\n\n| h |\n\n<!-- END_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->\nfooter\n"""

    block = sync_mod._extract_synced_block(text, path=Path("dummy.md"))

    assert block.startswith("## Response-policy invariants")
    assert "| h |" in block


def test_render_mirror_replaces_only_synced_region() -> None:
    mirror_text = """intro\n<!-- BEGIN_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->\nold\n<!-- END_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->\noutro\n"""

    rendered = sync_mod._render_mirror(mirror_text, "new block", path=Path("mirror.md"))

    assert rendered == """intro\n<!-- BEGIN_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->\n\nnew block\n\n<!-- END_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->\noutro\n"""
