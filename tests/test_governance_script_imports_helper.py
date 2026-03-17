from __future__ import annotations

from pathlib import Path


CANONICAL_GOVERNANCE_BASE_REF_SCRIPTS = {
    "all_green_gate.py",
    "validate_issue_links.py",
    "validate_issues.py",
}


def test_governance_scripts_use_shared_base_ref_helper() -> None:
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"

    for script in sorted(scripts_dir.glob("*.py")):
        is_governance_script = script.name in CANONICAL_GOVERNANCE_BASE_REF_SCRIPTS or script.name.startswith(
            "validate_issue"
        )
        if not is_governance_script:
            continue

        text = script.read_text(encoding="utf-8")
        assert "governance_base_ref" in text, f"{script.name} must import governance_base_ref for base-ref logic"
        assert "governance_resolve_base_ref" in text, f"{script.name} should route base-ref checks through the shared helper"
