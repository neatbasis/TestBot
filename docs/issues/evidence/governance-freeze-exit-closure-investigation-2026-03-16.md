# Governance freeze-exit closure investigation (2026-03-16)

> Issue linkage: `ISSUE-0022`
>
> Purpose: verify whether the prior closure investigation matches the **current repository implementation**, not just document narratives.

## 1) Recency and synchronization check

Chronology from git history (creation and latest update):

| File | Created (commit, time) | Latest change (commit, time) | Interpretation |
| --- | --- | --- | --- |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | `b021ad5`, 2026-03-16 16:59 +0200 | `f9f2431`, 2026-03-16 17:26 +0200 | Foundational diagnosis |
| `docs/issues/governance-control-surface-contract-freeze.md` | `f9f2431`, 2026-03-16 17:26 +0200 | same | Active canonical freeze contract |
| `docs/issues/evidence/governance-stabilization-checklist.md` | `f666901`, 2026-03-16 17:31 +0200 | `8e4fca2`, 2026-03-16 23:06 +0200 | Working stabilization tracker |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | `3702b32`, 2026-03-16 20:11 +0200 | `ed314ad`, 2026-03-16 23:00 +0200 | Narrative roll-up |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | `cbafbff`, 2026-03-16 23:54 +0200 | same | Newest synthesis artifact |

Verdict: the completion audit is **up to date by chronology**, and still intentionally not a freeze-exit proof artifact.

## 2) Code-grounded findings by closure area

## A + D) Validator ownership and duplication

### Canonical section checks

Observed implementations:

- `scripts/validate_issues.py` defines `contains_section(...)` and checks canonical sections inside `validate_issue_files(...)`.
- `scripts/validate_issue_links.py` defines `contains_schema_section(...)` and checks canonical sections inside `validate_issue_schema(...)`.
- `scripts/governance_rules.py` provides `parse_canonical_sections(...)` only; it does **not** provide a single shared canonical section presence-check function.

Result: canonical section presence logic is still implemented in more than one validator.

### PR-reference rule family

Observed implementations:

- `validate_issues.py` checks PR body only in `validate_pr_body(...)` and emits message:
  - `"Non-trivial PR description must include at least one ISSUE-XXXX reference."`
- `validate_issue_links.py` checks PR body and commit metadata in `validate_pr_and_commit_metadata(...)` and emits message:
  - `"Non-trivial PR metadata must include at least one issue ID (ISSUE-XXXX)."`

Result: both validators participate in PR-reference family checks, with overlapping intent and non-identical error wording.

### Ownership map existence

- No explicit rule-family ownership table was found in canonical docs or `governance_rules.py`.
- Existing docs mention ownership as a goal, but no implemented authoritative map currently exists.

Conclusion for A + D: prior investigation claim is **confirmed**; duplication/supersession risk remains reduced but not eliminated.

## B) Strict vs triage coverage matrix

### Ruleset option existence and branching

- Both validators expose `--ruleset {strict, triage}` with `strict` default.
- Branch points:
  - `validate_issues.py`: skips red-tag strict checks when `ruleset == triage`.
  - `validate_issue_links.py`: skips strict-only schema body/enum checks and red-tag generation check in triage mode.

### Test coverage shape

- No cross-validator shared-fixture matrix test was found that executes both validators in both modes against the same fixtures.
- Existing tests are largely per-validator unit tests.
- `tests/test_validate_issue_links.py` has no explicit strict-vs-triage divergence assertion.
- `tests/test_validate_issues.py` currently exercises strict behavior paths; explicit mode-difference assertions are not present.

Conclusion for B: ruleset capability exists, but explicit strict×triage×validator matrix coverage remains incomplete.

## C) Feature-status linkage normalization

### Current contract data usage

From `docs/qa/feature-status.yaml`:

- capabilities total: 9
- entries with `issue_ids`: 6
- entries with `open_issues` (compat alias): 6
- entries with `issue_keywords`: 9
- keyword-only entries (no `issue_ids` and no `open_issues`): 3
  - `time_aware_memory_ranking`
  - `external_source_ingestion`
  - `governance_readiness_gate`

### Fallback reachability in code

- `scripts/report_feature_status.py` linkage order is:
  1. `issue_ids`
  2. fallback alias `open_issues`
  3. keyword matching via `issue_keywords` with deprecation warning
- Because keyword-only capabilities still exist in repo data, fallback is currently reachable in normal execution.

### Warning/actionability status

- Structured warnings are emitted for keyword-only fallback usage.
- Running the report generated three deprecation warnings, one per keyword-only capability.
- No dedicated migration inventory table file exists yet that tracks remaining keyword-only entries as a maintained checklist artifact.

Conclusion for C: mechanism exists and warnings are actionable; migration is still incomplete.

## E) Governance hardening controls

### CI enforcement present in repo

- `.github/workflows/issue-link-validation.yml` runs `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` on every pull request.
- Repo contains `.github/PULL_REQUEST_TEMPLATE.md` with an `Issue: ISSUE-XXXX` section.

### Hardening controls missing or non-mechanized

- No `CODEOWNERS` file exists in repo root or `.github/`.
- No CI check was found that enforces PR dependency declaration/contract-delta declarations for governance control-surface changes.
- No in-repo mechanism was found that prevents concurrent non-stacked governance-surface PRs.

Conclusion for E: hardening is partially mechanized (one workflow + template), but key controls remain process-driven.

## F) Freeze contract integrity prerequisites

### Freeze status implementation

- Freeze contract exists as markdown: `docs/issues/governance-control-surface-contract-freeze.md`.
- `scripts/all_green_gate.py` encodes freeze-governed path sets and forces full governance checks when touched.
- No dedicated machine-readable freeze flag file was found that CI reads as a single freeze-state source.

### Merge blocking behavior

- No workflow was found that explicitly blocks governance-surface merges based on freeze-active state itself.
- Effective freeze enforcement is a combination of policy doc + selective governance checks, not a standalone “freeze lock” automation.

### Audit-to-code traceability and ISSUE-0022 presence

- Some checklist reconciliations are backed by tests/implementation (e.g., changed-path override constants and skip policy logic in `all_green_gate.py`).
- Other closure items remain narrative/open pending implementation (e.g., ownership singularization map, strict/triage matrix parity suite).
- `ISSUE-0022` appears in documentation and commit metadata; it does not currently appear in test names or machine-readable contract flags.

Conclusion for F: prerequisites remain incomplete for no-caveat freeze exit.

## 3) Updated closure status verdict

1. **Validator ownership & duplication:** open
2. **Strict vs triage matrix completeness:** open
3. **Feature-status linkage normalization:** partial/open
4. **Duplicate-intent supersession cleanup:** open
5. **Governance hardening controls:** partial/open
6. **Freeze-exit no-caveat statement readiness:** not yet eligible

Overall: prior investigation conclusions are **confirmed by code inspection** and should be strengthened with the code-grounded evidence above.

## 4) Recommended max-synergy execution order (unchanged, now code-validated)

1. Singularize rule ownership and remove duplicate enforcement paths.
2. Add strict-vs-triage parity/divergence matrix across both validators using shared fixtures.
3. Complete feature-status explicit-link migration and publish migration inventory table.
4. Mechanize hardening controls (CODEOWNERS/review gates/dependency declaration enforcement).
5. Perform freeze-exit evidence pass and publish freeze-lift statement without caveats.

## 5) Evidence commands used

```bash
git log --diff-filter=A --date=iso --pretty=format:'%h %ad %s' -- <evidence-files>
git log -1 --date=iso --pretty=format:'%h %ad %s' -- <evidence-files>

nl -ba scripts/validate_issues.py | sed -n '1,280p'
nl -ba scripts/validate_issue_links.py | sed -n '1,340p'
nl -ba scripts/validate_issue_links.py | sed -n '150,260p'
nl -ba scripts/validate_issue_links.py | sed -n '320,470p'
nl -ba scripts/governance_rules.py | sed -n '1,280p'
nl -ba scripts/all_green_gate.py | sed -n '220,360p'

nl -ba tests/test_validate_issues.py | sed -n '1,320p'
nl -ba tests/test_validate_issue_links.py | sed -n '1,520p'
rg -n "ruleset|triage|strict|contains_schema_section|issue_ids|open_issues|issue_keywords|deprecated issue_keywords" \
  scripts/report_feature_status.py tests/test_validate_issues.py tests/test_validate_issue_links.py tests/test_report_feature_status.py docs/qa/feature-status.yaml

python - <<'PY'
from pathlib import Path
import yaml
p=Path('docs/qa/feature-status.yaml')
data=yaml.safe_load(p.read_text())
cap=data.get('capabilities',[])
print('capabilities',len(cap))
print('with issue_ids',sum(1 for c in cap if c.get('issue_ids')))
print('with open_issues',sum(1 for c in cap if c.get('open_issues')))
print('with issue_keywords',sum(1 for c in cap if c.get('issue_keywords')))
print('keyword_only',sum(1 for c in cap if c.get('issue_keywords') and not c.get('issue_ids') and not c.get('open_issues')))
PY

python scripts/report_feature_status.py --json-output /tmp/feature-status-summary.json
python - <<'PY'
import json
s=json.load(open('/tmp/feature-status-summary.json'))
print('deprecated_keyword_warnings',sum('deprecated issue_keywords' in w for w in s.get('warnings',[])))
PY

nl -ba .github/workflows/issue-link-validation.yml
nl -ba .github/PULL_REQUEST_TEMPLATE.md
rg --files | rg -n 'CODEOWNERS|codeowners'

python scripts/validate_issues.py --all-issue-files --base-ref HEAD
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD
python scripts/all_green_gate.py
```
