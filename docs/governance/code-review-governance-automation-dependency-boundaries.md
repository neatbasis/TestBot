# Code Review: Governance Automation, Issue Tracking, and Reporting Scripts

Checklist baseline: `docs/governance/python-code-review-checklist-dependency-boundaries.md`.

## Scope reviewed
- `scripts/all_green_gate.py`
- `scripts/validate_issue_links.py`
- `scripts/validate_issues.py`
- `scripts/report_feature_status.py`
- Related unit tests in `tests/test_validate_issue_links.py`, `tests/test_validate_issues.py`, `tests/test_report_feature_status.py`

## Findings

### 1) Inconsistent PR issue-link contract across validators — **🟠 Major**
- `validate_issue_links.py` accepts any `ISSUE-XXXX` token in non-trivial PR metadata.
- `validate_issues.py` previously required the stricter `Issue: ISSUE-XXXX` phrase.
- This created a governance boundary mismatch: same policy intent, different acceptance contract.
- **Action taken in this change set:** aligned `validate_issues.py` to accept any `ISSUE-XXXX`, matching `validate_issue_links.py`.

### 2) Non-triviality threshold mismatch for PR metadata — **🟠 Major**
- `validate_issue_links.py` treated non-trivial text as >= 12 words and ignored `[trivial]`/`#trivial`.
- `validate_issues.py` previously used >= 15 words and only recognized `#trivial`.
- This created coupling drift in the shared policy seam.
- **Action taken in this change set:** aligned `validate_issues.py` to >= 12 words and both trivial markers.

### 3) Duplicate policy logic between `validate_issue_links.py` and `validate_issues.py` — **🟡 Minor**
- Both scripts independently implement base-ref fallback and canonical section parsing.
- This is maintainable today, but high drift risk over time.
- **Recommendation:** factor shared policy primitives into a small internal module (for example, `scripts/_internal/governance_policy.py`) and keep CLI wiring in script entrypoints.

### 4) Boundary encapsulation is generally clean — **🟢 Suggestion**
- Side-effectful operations are contained in `main()` and helper functions, not on import.
- Dependency directions are mostly one-way (scripts read docs/artifacts and invoke git/subprocess).
- Good use of typed local structures in `validate_issue_links.py` (`ValidationFailure`) and `report_feature_status.py` dataclasses.

### 5) Test seam coverage status — **🟢 Suggestion**
- Existing tests cover ref fallback and key report wiring.
- **Action taken in this change set:** added targeted tests for the newly aligned PR triviality and issue ID acceptance behavior in `tests/test_validate_issues.py`.
- **Recommendation:** add one end-to-end fixture test that runs both validators against the same synthetic PR body to prevent future contract divergence.

## Dependency-boundary checklist summary
- **Module/package boundaries:** Pass with minor duplication caveat.
- **Dependency direction:** Pass; no direct cycle evidence in reviewed scripts.
- **Interface/contract explicitness:** Improved by this change; still room to centralize shared contract constants.
- **Coupling smell audit:** Mild duplication smell only.
- **Governance hygiene:** Good; scripts are traceable and policy-driven.
- **Boundary test coverage:** Adequate and improved in this patch.
- **CI/static gates:** Not fully reviewed here (out of scope for tooling config files).

## Net assessment
Current governance automation is structurally sound, with the primary risk being policy drift across parallel validators. This patch resolves the most immediate drift points and tightens test coverage around that contract.
