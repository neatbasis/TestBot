"""Shared governance helper for base-ref resolution and degraded commit-traceability policy."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable, Final

MISSING_REQUESTED_BASE_REF_NOTE: Final[str] = (
    "Base ref '{ref}' does not exist. Provide a valid --base-ref (for example origin/main, HEAD~1, or HEAD)."
)
ORIGIN_MAIN_FALLBACK_NOTE: Final[str] = (
    "Base ref 'origin/main' is unavailable; falling back to '{fallback}'.\n"
    "       This is expected in Codex task containers or shallow CI clones.\n"
    "       Governance diff checks are running against a reduced baseline.\n"
    "       Commit-traceability checks may still fail closed unless degraded mode is explicitly allowed.\n"
    "       For authoritative results, run locally with 'git fetch origin main' first. "
    "(Unless you are ChatGPT/Codex!)"
)
NO_USABLE_BASE_REF_NOTE: Final[str] = (
    "Could not resolve base ref 'origin/main' or fallbacks (HEAD~1, HEAD). "
    "Governance diff checks will run against a reduced baseline and all issue files may be validated."
)
EPHEMERAL_ORIGIN_MAIN_REF: Final[str] = "refs/codex/origin-main"
ORIGIN_MAIN_RECOVERY_REUSED_NOTE: Final[str] = (
    "Base ref 'origin/main' is unavailable; using existing recovered ref 'refs/codex/origin-main'."
)
ORIGIN_MAIN_RECOVERY_FETCHED_NOTE: Final[str] = (
    "Base ref 'origin/main' is unavailable; recovered from GIT_ORIGIN_URL into 'refs/codex/origin-main'."
)


def git_ref_exists(ref: str, *, repo_root: Path) -> bool:
    """Return whether a Git ref exists in the given repository root."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def allow_remote_base_ref_recovery() -> bool:
    """Return whether remote base-ref recovery is enabled by environment policy."""
    return os.getenv("ALLOW_REMOTE_BASE_REF_RECOVERY", "").strip().lower() in {"1", "true", "yes", "on"}


def fetch_origin_main_recovery_ref(*, repo_root: Path, origin_url: str) -> bool:
    """Attempt to fetch origin main into a local ephemeral recovery ref."""
    result = subprocess.run(
        ["git", "fetch", "--no-tags", origin_url, f"main:{EPHEMERAL_ORIGIN_MAIN_REF}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_base_ref(
    base_ref: str,
    *,
    ref_exists: Callable[[str], bool],
    repo_root: Path | None = None,
) -> tuple[str | None, list[str]]:
    """Resolve base ref using canonical fallback order and canonical note wording."""
    notes: list[str] = []
    if ref_exists(base_ref):
        return base_ref, notes

    if base_ref != "origin/main":
        return None, [MISSING_REQUESTED_BASE_REF_NOTE.format(ref=base_ref)]

    if ref_exists(EPHEMERAL_ORIGIN_MAIN_REF):
        return EPHEMERAL_ORIGIN_MAIN_REF, [ORIGIN_MAIN_RECOVERY_REUSED_NOTE]

    if repo_root is not None and allow_remote_base_ref_recovery():
        origin_url = os.getenv("GIT_ORIGIN_URL", "").strip()
        if origin_url and fetch_origin_main_recovery_ref(repo_root=repo_root, origin_url=origin_url):
            if ref_exists(EPHEMERAL_ORIGIN_MAIN_REF):
                return EPHEMERAL_ORIGIN_MAIN_REF, [ORIGIN_MAIN_RECOVERY_FETCHED_NOTE]

    for fallback in ("HEAD~1", "HEAD"):
        if ref_exists(fallback):
            notes.append(ORIGIN_MAIN_FALLBACK_NOTE.format(fallback=fallback))
            return fallback, notes

    notes.append(NO_USABLE_BASE_REF_NOTE)
    return None, notes


def commit_traceability_failure(
    *,
    requested_base_ref: str,
    effective_base_ref: str | None,
    allow_degraded_commit_traceability: bool,
) -> tuple[str, str] | None:
    """Return fail-closed message+hint when commit traceability cannot run authoritatively."""
    if effective_base_ref is None:
        return (
            f"Commit-history ISSUE linkage requires a resolvable base ref; could not resolve '{requested_base_ref}'.",
            "Fetch the canonical base ref (for example 'git fetch origin main') and rerun the validator.",
        )

    if requested_base_ref == effective_base_ref or allow_degraded_commit_traceability:
        return None

    if requested_base_ref == "origin/main" and effective_base_ref == EPHEMERAL_ORIGIN_MAIN_REF:
        return None

    return (
        "Commit-history ISSUE linkage checks fail closed when running against a fallback base ref.",
        (
            f"Requested '{requested_base_ref}' but resolved '{effective_base_ref}'. Fetch the requested ref or rerun with "
            "--allow-degraded-commit-traceability for non-authoritative container checks."
        ),
    )
