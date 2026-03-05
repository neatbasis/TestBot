# ISSUE-0003: README repository layout drift vs actual tree

- **ID:** ISSUE-0003
- **Title:** README repository layout drift vs actual tree
- **Status:** resolved
- **Severity:** amber
- **Owner:** Sebastian Mäki (@NeatBasis, Documentation Maintainer)
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 2
- **Principle Alignment:** traceable, user-centric

## Problem Statement

Resolved. README repository layout now distinguishes current files from planned placeholders and aligns with tracked paths.

## Evidence

- README `Current repository tree` lists `features/` and `scripts/eval_recall.py`, matching the current repository.
- README separately marks planned items (`prompts.py`, `scripts/run_sat.sh`) under `Planned (not in repo yet)`.
- Contributing docs include a docs QA checklist item requiring file-tree examples to match current layout.

## Impact

- Restored documentation trust for new contributors.
- Reduced setup/debug time from path mismatch.

## Acceptance Criteria

1. ✅ README repository layout matches actual tracked files.
2. ✅ Planned/not-yet-created files are clearly marked as planned.
3. ✅ Docs review checklist includes a file-reference integrity check.

## Work Plan

- Keep README tree updates coupled with structural repository changes.
- Continue running docs path validation in docs-focused PRs.

## Verification

- Command: `rg --files features scripts README.md`
  - Expected: output includes files referenced in README tree.
- Command: `python scripts/validate_markdown_paths.py`
  - Expected: `All markdown local file/path references look valid.`

## Closure Notes

- 2026-03-04: Closed as resolved after README/tree reconciliation and docs QA checklist alignment.
- Residual risk: low; future drift possible if repository structure changes without corresponding README updates.
