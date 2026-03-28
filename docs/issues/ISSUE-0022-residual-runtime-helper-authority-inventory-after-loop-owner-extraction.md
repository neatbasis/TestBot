# ISSUE-0022: Residual runtime helper authority inventory after loop-owner extraction

- **ID:** ISSUE-0022
- **Title:** Residual runtime helper authority inventory after loop-owner extraction
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-28
- **Target Sprint:** Sprint 6
- **Canonical Cross-Reference:** ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md, ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md
- **Principle Alignment:** contract-first, invariant-driven, deterministic, traceable, ci-enforced

## Problem Statement

`testbot.entrypoints.runtime_loop.run_chat_loop` is now the canonical loop sequencing owner, but helper-level runtime authority remains concentrated behind compatibility delegation in `testbot.sat_chatbot_memory_v2`. Without a residual-authority inventory and explicit ranking, follow-up extraction can regress into utility-motion instead of authority retirement.

## Evidence

- Runtime-loop seam extraction evidence was recorded under ISSUE-0021 with `entrypoints/runtime_loop.py` declared as loop-owner and `runtime_legacy_bridge` narrowed to compatibility-facing delegation.
- Current loop owner still depends on compatibility delegation into helper-level monolith behavior (`sat_chatbot_memory_v2`) for pipeline invocation, telemetry/debug emission, pending-ingestion update handling, commit persistence dispatch, and runtime turn-bridge surfaces.
- Focused runtime-loop regression coverage currently protects short-circuit and delegation behavior but does not yet enforce a residual-helper authority ranking contract.

## Impact

- Residual authority ambiguity can re-introduce split ownership across runtime loop and compatibility monolith layers.
- Future extraction PRs may optimize line movement while leaving policy authority concentrated in legacy helpers.
- Reviewers lose a deterministic rubric for choosing the next seam by ownership impact.

## Acceptance Criteria

- [ ] Residual helper-level runtime authorities reachable from `entrypoints/runtime_loop` are enumerated with file-level symbol references and responsibility statements.
- [ ] The inventory includes authority-density ranking with explicit justification for top seam selection.
- [ ] A successor implementation issue is opened (or this issue is updated) for exactly one highest-leverage seam extraction.
- [ ] A deterministic anti-regression guard is added (test or validator assertion) that prevents monolith re-ownership of loop sequencing.
- [ ] Closure evidence includes governance validator success and canonical gate status (including explicit treatment of unrelated pre-existing failures when present).

## Work Plan

1. Build a residual-authority table for helper clusters currently delegated from `entrypoints/runtime_loop`.
2. Rank helper clusters by authority density (policy ownership concentration, cross-cutting blast radius, and ambiguity reduction potential).
3. Select one top-ranked helper cluster and define the narrow extraction boundary for the next PR.
4. Add an anti-regression contract asserting loop sequencing remains owned by `entrypoints/runtime_loop`.
5. Execute targeted extraction PR with focused tests and update ISSUE-0021/ISSUE-0013 cross-links.

## Verification

```bash
python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
python scripts/all_green_gate.py
```

## Closure Notes

Pending.
