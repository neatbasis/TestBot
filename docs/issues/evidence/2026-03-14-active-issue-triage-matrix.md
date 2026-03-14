# Active issue triage matrix (dependency-focused)

- **Date:** 2026-03-14
- **Scope seed sources:**
  - `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
  - `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
  - `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
  - `docs/issues/RED_TAG.md`
- **Prioritization rule used for top investigations:** highest remaining uncertainty + highest dependency impact on the active chain `ISSUE-0008 -> ISSUE-0011 -> ISSUE-0012 -> ISSUE-0014 -> ISSUE-0015`, routed through `ISSUE-0013`.

## Triage matrix

| issue id | blocker/dependent role | unknowns requiring investigation | required evidence artifact | owner | due date |
|---|---|---|---|---|---|
| ISSUE-0013 | Routing anchor (open/blocked pending evidence); downstream closure blocked by ISSUE-0014 + ISSUE-0015 gates | Whether AC-0013-11 exit conditions (A/B/C) are jointly satisfied from current branch evidence rather than mixed historical snapshots; whether optional KPI warning debt is still correctly treated as blocker evidence in this chain | `docs/issues/evidence/2026-03-14-issue-0013-ac-0013-11-dependency-reconciliation.md` | platform-qa | 2026-03-16 |
| ISSUE-0014 | **Blocker** (identity-continuity behavioral gate for ISSUE-0013 AC-0013-11) | Whether rewrite-stage semantic inversion is still present in current runtime; whether retrieval activates on immediate self-reference recall under continuity artifacts; whether commit promotion writes confirmed identity facts deterministically | `docs/issues/evidence/2026-03-14-issue-0014-phase1-closure-proof-refresh.md` | platform-qa | 2026-03-16 |
| ISSUE-0015 | **Dependent** governance close-order gate | Whether closure discipline can still be bypassed by structural-only proof; whether ISSUE-0013/0014/0015 + RED_TAG lifecycle wording and dependency labels remain fully synchronized after refreshed evidence | `docs/issues/evidence/2026-03-14-issue-0015-governance-close-order-audit.md` | release-governance | 2026-03-21 |
| ISSUE-0012 | Parallel stream (delivery-plan governance) | Whether staged delivery checkpoints still map to the latest blocker-state reality (especially ISSUE-0014 Phase 1 and AC-0013-11 dependencies), without over-claiming readiness | `docs/issues/evidence/2026-03-14-issue-0012-delivery-plan-checkpoint-sync.md` | release-governance | 2026-03-21 |
| ISSUE-0011 | Blocker (observability gate) | Whether analytics input-coverage diagnostics can reliably surface semantic misroute signatures (rewrite drift, retrieval skip rationale, commit denial reasons) for this regression class | `docs/issues/evidence/2026-03-14-issue-0011-observability-coverage-gap-review.md` | platform-qa | 2026-03-21 |
| ISSUE-0008 | Blocker (upstream quality gate) | Whether deterministic intent-grounding guarantees still prevent early-route drift regression from re-entering canonical flow for identity/self-reference turns | `docs/issues/evidence/2026-03-14-issue-0008-intent-grounding-regression-check.md` | runtime-pipeline | 2026-03-21 |

## Top 4 prioritized investigation tasks

1. **ISSUE-0014 Phase 1 behavioral closure-proof refresh (highest uncertainty + direct blocker impact).**
   - Why first: unresolved semantic-correctness uncertainty directly blocks ISSUE-0013 AC-0013-11 and ISSUE-0015 closure.
   - Evidence path expectation: `docs/issues/evidence/2026-03-14-issue-0014-phase1-closure-proof-refresh.md`.
2. **ISSUE-0013 AC-0013-11 dependency reconciliation update (high uncertainty + routing-anchor impact).**
   - Why second: routing anchor governs dependency interpretation for all linked streams; stale/mixed snapshot interpretation can invalidate close-order decisions.
   - Evidence path expectation: `docs/issues/evidence/2026-03-14-issue-0013-ac-0013-11-dependency-reconciliation.md`.
3. **ISSUE-0015 governance close-order audit (medium-high uncertainty + high dependency impact).**
   - Why third: prevents premature closure under structural-only evidence and enforces synchronized blocker/dependent language across artifacts.
   - Evidence path expectation: `docs/issues/evidence/2026-03-14-issue-0015-governance-close-order-audit.md`.
4. **ISSUE-0011 observability coverage gap review (medium uncertainty + high recurrence-prevention impact).**
   - Why fourth: determines whether monitoring can detect reintroduction of the same semantic/routing defect class after fixes.
   - Evidence path expectation: `docs/issues/evidence/2026-03-14-issue-0011-observability-coverage-gap-review.md`.

## Notes

- Due dates and owners above are aligned to the currently documented dependency-gate ownership and review cadence in ISSUE-0013/0014/0015 and RED_TAG.
- This note is intentionally focused on active dependency-chain triage readiness rather than broad issue inventory expansion.
