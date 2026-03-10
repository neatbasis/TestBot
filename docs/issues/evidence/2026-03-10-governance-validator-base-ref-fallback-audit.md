# Governance validator base-ref fallback audit (2026-03-10)

## Context

Requested governance readiness commands were executed with canonical `--base-ref origin/main` first, then explicitly rerun with `--base-ref HEAD~1` per `docs/issues.md` fallback workflow because `origin/main` was unavailable in this environment.

## Command run log

### 1) Canonical issue-link validator run (default base ref)

Command:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
```

Output:

```text
[WARN] Base ref 'origin/main' is unavailable; falling back to 'HEAD~1'.
Governance validation passed.
```

Result: **pass** (with automatic base-ref fallback warning).

### 2) Canonical issue-structure validator run (default base ref)

Command:

```bash
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
```

Output:

```text
[INFO] No --pr-body-file provided; skipping PR description validation.
[WARN] Base ref 'origin/main' is unavailable; falling back to 'HEAD~1'.
Issue validation passed.
```

Result: **pass** (with automatic base-ref fallback warning).

### 3) Explicit fallback rerun for issue-link validator

Command:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1
```

Output:

```text
Governance validation passed.
```

Result: **pass**.

### 4) Explicit fallback rerun for issue-structure validator

Command:

```bash
python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1
```

Output:

```text
[INFO] No --pr-body-file provided; skipping PR description validation.
Issue validation passed.
```

Result: **pass**.

## Why fallback was required

`origin/main` is unavailable in the current local environment, so both validators reported the documented warning and auto-fell back to `HEAD~1`. This behavior matches the fallback policy in `docs/issues.md` and was additionally validated by explicit `HEAD~1` reruns.
