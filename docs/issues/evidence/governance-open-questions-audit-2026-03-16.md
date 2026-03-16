# Governance open questions audit (2026-03-16)

> Scope: targeted audit for six open governance stabilization questions.
>
> Related freeze/control docs:
>
> - `docs/issues/governance-control-surface-contract-freeze.md`
> - `docs/issues/evidence/governance-stabilization-checklist.md`
> - `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`

## 1) Baseline migration: legacy issue files vs current Issue State contract

### Current measured result

- **Legacy issue files violating current Issue State contract: `0`**.
- `python scripts/validate_issues.py --all-issue-files --base-ref HEAD` passes.
- Direct inventory of all `docs/issues/ISSUE-*.md` files shows:
  - every issue has `Issue State: governed_execution`;
  - statuses are within canonical governed set (`open`, `in_progress`, `blocked`, `resolved`, `closed`).

### Minimal safe migration plan

Since current violations are zero, migration should be preventive rather than corrective:

1. Keep `scripts/validate_issues.py --all-issue-files` as the contract gate for issue-state/schema drift.
2. Add a deterministic test fixture with one intentionally legacy status/state pair (e.g., `Issue State: triage_intake` + `Status: in_progress`) to preserve rejection behavior.
3. Optionally tighten `scripts/report_feature_status.py::collect_open_issues()` to stop treating legacy status strings (`todo`, `triaged`) as open-like for downstream linkage/reporting semantics.
4. Keep freeze checklist row as `inventory complete` until #2 and #3 are reconciled and verified.

## 2) Validator boundary audit: `validate_issues.py` vs `validate_issue_links.py`

### Explicitly duplicated/overlapping checks (beyond manifest handling)

1. **Canonical schema-section presence checks overlap**
   - `validate_issues.py` checks canonical sections/fields via `contains_section(...)` and policy-derived section list.
   - `validate_issue_links.py` also checks canonical sections via `contains_schema_section(...)` and policy-derived section list.
2. **PR metadata issue-reference checks overlap**
   - `validate_issues.py` checks non-trivial PR body has `ISSUE-XXXX` reference.
   - `validate_issue_links.py` also checks non-trivial PR body for issue reference.
3. **Issue-file discovery and base-ref range logic overlap**
   - both scripts implement `--all-issue-files` vs base-ref-added-file selection behavior.

### Non-overlapping ownership that is already clear

- `validate_issue_links.py` uniquely owns:
  - commit-message issue-reference validation,
  - ID/filename alignment,
  - required field non-placeholder enforcement,
  - enum value enforcement (`Status`, `Severity`),
  - required section body non-placeholder enforcement,
  - RED_TAG generated-content parity check.
- `validate_issues.py` uniquely owns:
  - `Issue State` model transition rule (`triage_intake` only with `Status: open`),
  - red-tag owner/target-sprint policy checks in strict mode.

### Minimal ownership clarification to ratify

- Make `validate_issues.py` the sole issue state + schema-transition owner.
- Make `validate_issue_links.py` the sole linkage/reference/metadata owner.
- Remove duplicated section-presence and PR-body issue-reference checks from one side after tests are updated.

## 3) Gate governed-surface matrix for skip-reduction disablement

### Freeze requirement

Freeze contract requires: if any frozen control-surface file (or governed semantic fixture/config) changes, skip reduction must be disabled and full governance checks must run.

### Current implementation reality

`apply_governance_skip_policy()` currently decides issue-validator/invariant skips from:

- issue-validator scope prefixes:
  - `docs/issues/`, `docs/governance/`, `docs/releases/`, `docs/qa/`
- issue-validator exact path:
  - `docs/issues.md`
- invariant scope prefixes:
  - `docs/directives/`, `docs/invariants/`
- invariant exact path:
  - `docs/invariants.md`

### Missing from an explicit freeze-aligned governed matrix

Not explicitly represented as force-full-governance triggers in current gate logic:

- `scripts/all_green_gate.py`
- `scripts/validate_issue_links.py`
- `scripts/validate_issues.py`
- `scripts/governance_rules.py`
- `scripts/triage_router.py`
- `tests/test_all_green_gate.py`
- `tests/test_validate_issue_links.py`
- `tests/test_validate_issues.py`
- `docs/qa/triage-routing.yaml`
- `artifacts/verification/*` and similar governed semantic fixtures called out by freeze prose.

### Potentially over-included paths relative to freeze text

- `docs/governance/` and `docs/releases/` are included in skip-trigger prefixes in code, but are not named as frozen surfaces in the freeze directive list.
- These may be acceptable conservative inclusions, but ownership rationale should be documented explicitly so this is not ambiguous.

## 4) RED_TAG derivation parity audit

### Current measured result

- `python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD` passes, including generated RED_TAG parity check.
- `docs/issues/RED_TAG.md` currently matches generated semantics for open-like red issues.

### Edge-case drift risks still present

1. RED_TAG generator uses open-like statuses `{open, in_progress, blocked}`.
2. `report_feature_status.py` still treats legacy statuses `{todo, triaged}` as open-like for feature linkage/reporting.
3. If legacy statuses ever reappear in issue files, RED_TAG and feature-status semantics can diverge silently (RED_TAG excludes them; feature report may include them).

## 5) Feature-linkage precedence + lingering old-behavior signals

### Actual precedence in code

1. Primary linkage: `issue_ids`.
2. Compatibility fallback: `open_issues` (legacy alias).
3. If neither exists, fallback linkage by `issue_keywords` (with deprecation warning).
4. Suggestions (`scripts/suggest_issue_links.py`) run only when neither explicit list is present.

### Fixtures/examples still implying legacy behavior

- Contract examples still contain `open_issues` and `issue_keywords` fields in `docs/qa/feature-status.yaml`.
- Tests intentionally cover keyword fallback and `open_issues` compatibility, so old behavior remains active-by-design.

## 6) Triage router freeze-conformance audit

### Current state

`triage_router.py` consumes gate summary JSON check failures, but it also **reinterprets** semantics by:

- inferring owner/severity from changed-directory prefixes,
- applying stage defaults,
- elevating overall severity from local routing logic.

This goes beyond pure consumption of stabilized gate outputs and matches the freeze/checklist concern about potential reinterpretation risk.

### Minimal safe conformance direction

1. Treat gate summary statuses as authoritative input (no status reinterpretation).
2. Keep routing as annotation-only policy layer, with explicit precedence documented in `docs/qa/triage-routing.yaml`.
3. Add deterministic tests proving router behavior does not alter upstream pass/fail meaning.

## Requested source recency check (git history)

Per-file last-change metadata:

- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
  - commit: `f9f24313a5d42f49a596f1410eed65112d1256ea`
  - date: `2026-03-16 17:26:02 +0200`
- `docs/issues/evidence/governance-stabilization-checklist.md`
  - commit: `d4a37588f20e8d68a2bcb5710dd971cb3440d9b1`
  - date: `2026-03-16 19:51:11 +0200`
- `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
  - commit: `b5ee10317420d571689adaa8d6af65d365ba0dd6`
  - date: `2026-03-16 21:43:11 +0200`
- `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
  - commit: `3702b32ca98c844916a2a86fc1ab8c4aa6bfa9ae`
  - date: `2026-03-16 20:11:28 +0200`

## Evidence commands used

```bash
python scripts/validate_issues.py --all-issue-files --base-ref HEAD
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD
python - <<'PY'
from pathlib import Path
import re
root=Path('docs/issues')
rows=[]
for p in sorted(root.glob('ISSUE-*.md')):
    t=p.read_text()
    st=re.search(r'^- \*\*Status:\*\*\s*([^\n]+)',t,re.M)
    isd=re.search(r'^- \*\*Issue State:\*\*\s*([^\n]+)',t,re.M)
    rows.append((p.name, st.group(1).strip() if st else '', isd.group(1).strip() if isd else ''))
print('total',len(rows))
for r in rows:
    print('\t'.join(r))
PY
nl -ba scripts/validate_issues.py | sed -n '1,260p'
nl -ba scripts/validate_issue_links.py | sed -n '1,520p'
nl -ba scripts/all_green_gate.py | sed -n '1,680p'
nl -ba scripts/triage_router.py | sed -n '1,260p'
nl -ba scripts/report_feature_status.py | sed -n '140,210p'
nl -ba scripts/suggest_issue_links.py | sed -n '1,180p'
nl -ba scripts/generate_red_tag_index.py | sed -n '1,180p'
nl -ba docs/issues/governance-control-surface-contract-freeze.md | sed -n '1,220p'
git log -1 --date=iso --pretty=format:'%H%n%ad%n%s' -- docs/issues/evidence/coordination-failure-contract-drift-matrix.md
git log -1 --date=iso --pretty=format:'%H%n%ad%n%s' -- docs/issues/evidence/governance-stabilization-checklist.md
git log -1 --date=iso --pretty=format:'%H%n%ad%n%s' -- docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md
git log -1 --date=iso --pretty=format:'%H%n%ad%n%s' -- docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md
```
