# ISSUE-0003: README repository layout drift vs actual tree

- **ID:** ISSUE-0003
- **Title:** README repository layout drift vs actual tree
- **Status:** open
- **Severity:** amber
- **Owner:** unassigned
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 2
- **Principle Alignment:** traceable, user-centric

## Problem Statement

README lists files that are not present in the repository, causing documentation trust drift.

## Evidence

- README layout lists `src/testbot/prompts.py`.
- README layout lists `scripts/run_sat.sh`.
- These files are absent from current repository tree.

## Impact

- New contributors lose confidence in docs.
- Setup/debug time increases due to mismatch.

## Acceptance Criteria

1. README repository layout matches actual tracked files.
2. Planned/not-yet-created files are clearly marked as planned.
3. Docs review checklist includes a file-reference integrity check.

## Work Plan

- Update repository layout block.
- Add docs QA check for path validity.

## Verification

- Compare `rg --files` output against documented layout entries.

## Closure Notes

- _Pending alignment update._

