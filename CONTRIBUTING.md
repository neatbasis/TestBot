# Contributing

Thanks for contributing to TestBot.

Canonical turn-pipeline triage note: track pipeline defect elimination and delivery status in
[`docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).
Use ISSUE-0012 only as linked historical delivery-planning context.

## Docs QA checklist

When updating docs, complete this lightweight checklist before opening a PR:

- [ ] File tree examples match the current repository layout.
- [ ] Commands are runnable as written from the documented context.
- [ ] Required terms match the canonical glossary in `docs/directives/terms.md`.

Optional validation for markdown links/paths:

```bash
python scripts/validate_markdown_paths.py
```

Issue workflow validation (CI-friendly):

```bash
# Validate PR body metadata and newly added docs/issues files.
python scripts/validate_issue_links.py --pr-body-file .github/PULL_REQUEST_BODY.md --base-ref origin/main

# Validate all existing issue files locally.
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
```


## Required before merge

Run this required governance check (same command used by CI):

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
```

## Issue linkage requirements (mandatory)

For any **non-trivial behavior change** or **architecture-impacting change**:

- PR metadata (title/body text) with non-trivial content must include at least one issue reference token matching `ISSUE-XXXX`.
- Non-trivial commit metadata must include at least one issue reference token matching `ISSUE-XXXX`.
- If an issue has `Severity: red`, it must have a concrete `Owner`, concrete `Target Sprint`, and status-consistent placement in `docs/issues/RED_TAG.md` (`Active` for `open/in_progress/blocked`, `Resolved` for `resolved/closed`).
- New/updated issue files in `docs/issues/` must conform to the canonical schema declared in `docs/issues.md`, with all required canonical fields non-placeholder and required section bodies non-empty.

Failure mode when missing linkage or schema consistency:

- `python scripts/validate_issue_links.py` exits non-zero.
- CI merge gate must fail until issue linkage and issue governance data are corrected.
