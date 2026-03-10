# Red-Tag Issues

This file indexes all `severity: red` issues requiring escalated visibility.

## Representation policy

- `RED_TAG.md` is authoritative only for issues whose canonical file currently declares `Severity: red`.
- If an issue is reopened or rescoped as non-red (for example, `amber`), remove it from `Active`/`Resolved` red-tag lists immediately.
- Non-red follow-up lifecycle history may be captured in an archival note section, but that section must be explicitly labeled as out-of-scope for active red-tag status.

## Canonical pipeline routing note

- Canonical pipeline defects must be tagged and escalated against ISSUE-0013 first; link dependent issue IDs only after ISSUE-0013 routing is recorded.
- ISSUE-0013 may remain `Severity: amber` while still acting as canonical routing anchor; only `Severity: red` issues belong in Active/Resolved lists below.

## Recurring triage note template

Use this note under each red-tag issue entry whenever status changes or during scheduled triage:

```
- Last reviewed: YYYY-MM-DD
- Next review due: YYYY-MM-DD
- KPI evidence: docs/issues/evidence/sprint-<NN>-kpi-review.md
- Decision notes: <decision, rationale, and any escalation/rollback updates>
```

KPI evidence updates are mandatory for red-tag triage. If any KPI guardrail fails, include owner + due date and escalation/rollback intent in both the evidence note and decision notes.


KPI warning-mode governance policy is defined in `docs/testing.md` under [KPI guardrail mode policy (authoritative)](../testing.md#kpi-guardrail-mode-policy-authoritative). Use that policy as the canonical source for allowed modes, default rationale, promotion criteria, and persistent-warning issue-linkage requirements.


## KPI guardrail mode decision (authoritative triage posture)

- **Selected mode:** warning mode (`--kpi-guardrail-mode optional`).
- **Operational rule:** for active red-tag entries, warning-mode KPI results are blocker evidence until each warning has explicit issue linkage with owner + due date.
- **Active warning debt linkage (snapshot `2026-03-10T20:32:23Z`):** `qa_validate_kpi_guardrails` -> **Owner: platform-qa**, **Due: 2026-03-17** (triage review + mitigation update), with lifecycle synchronization accountability **Owner: release-governance**, **Due: 2026-03-17** across ISSUE-0013/0014/0015/RED_TAG.

## KPI warning debt vs blocker interpretation

- For `Severity: red` issues and blocker/dependent closure paths, persistent KPI guardrail warnings are treated as **blocker evidence** until mitigation is issue-linked with owner + due date.
- For non-red (`amber`/`green`) issues, KPI warnings in optional mode can be tracked as **accepted debt** only when the warning is linked to an active issue record with owner, due date, and mitigation plan.
- Do not mark issues `resolved`/`closed` while unresolved KPI warnings remain unlinked.

## Active dependency gate (consistency contract)

- Dependency order/state terminology must match ISSUE-0013 current execution order: ISSUE-0008 (**blocker**) -> ISSUE-0011 (**blocker**) -> ISSUE-0012 (**parallel stream**) -> ISSUE-0014 (**blocker**) -> ISSUE-0015 (**dependent**).
- ISSUE-0013 is the routing anchor for this chain; all linked issue files and RED_TAG entries must use the same blocker/dependent/parallel-stream labels.
- Closure of ISSUE-0015 remains open/blocked pending evidence until blocker conditions are met (ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 share one closure condition: deterministic evidence for identity semantic preservation, retrieval activation on immediate self-reference recall, and confirmed identity fact promotion at commit, plus reproducible CLI traces and canonical gate evidence).
- If any blocker is unresolved, keep ISSUE-0015 in the Active red-tag list and avoid resolved-language in related issue files.
- 2026-03-10 lifecycle sync note: canonical gate snapshot `2026-03-10T20:32:23Z` reports `status=failed`; lifecycle language across ISSUE-0013/0014/0015/RED_TAG is synchronized to blocker/dependent/parallel stream and open/blocked pending evidence posture with failing checks `product_behave`, `qa_pytest_not_live_smoke`, `qa_validate_invariant_sync` and warning check `qa_validate_kpi_guardrails`.
- ISSUE-0017 (amber) tracks pending-lookup fallback normalization for answer-commit invariants and must stay text-consistent with ISSUE-0010/INV-002 wording; this does not alter the active red-tag blocker/dependent chain unless ISSUE-0013 dependency evidence changes.

## Active

- Lifecycle sync refreshed on 2026-03-10 for gate snapshot `2026-03-10T20:32:23Z` (vocabulary normalized to blocker/dependent/parallel stream/open/blocked pending evidence and failed gate posture).

- ISSUE-0015 — **Open-issue review identifies ISSUE-0014 quality/governance gaps that could permit partial-fix closure**: Open red-tag governance hardening issue. Lifecycle interpretation: remains open/red until dependency exit conditions are met in ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 (identity semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit).
  - Last reviewed: 2026-03-10
  - Next review due: 2026-03-17
  - KPI evidence: artifacts/all-green-gate-summary.json
  - Decision notes: Dependency chain vocabulary remains synchronized; ISSUE-0015 stays open/blocked pending evidence because gate snapshot `2026-03-10T20:32:23Z` is failed (failing checks: `product_behave`, `qa_pytest_not_live_smoke`, `qa_validate_invariant_sync`; warning: `qa_validate_kpi_guardrails`; first failing commands: `product -> /root/.pyenv/versions/3.11.14/bin/python -m behave`, `qa -> /root/.pyenv/versions/3.11.14/bin/python -m pytest -m 'not live_smoke'`). KPI warning debt owner/due linkage: **Owner: platform-qa; Due: 2026-03-17** (with lifecycle wording sync follow-through by **release-governance; Due: 2026-03-17**).
- ISSUE-0014 — **CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion**: Open red-tag regression; evidence indicates rewrite-stage semantic inversion and self-reference misrouting prevent retrieval activation and confirmed-user-fact promotion. This is a blocking dependency for ISSUE-0013 AC-0013-11 and ISSUE-0015 closure gates.
  - Last reviewed: 2026-03-10
  - Next review due: 2026-03-17
  - KPI evidence: artifacts/all-green-gate-summary.json
  - Decision notes: ISSUE-0014 remains a blocker in the active chain; lifecycle wording is open/blocked pending evidence and aligned to gate snapshot `2026-03-10T20:32:23Z` (`status=failed`, failing checks: `product_behave`, `qa_pytest_not_live_smoke`, `qa_validate_invariant_sync`, warning check: `qa_validate_kpi_guardrails`). KPI warning debt owner/due linkage: **Owner: platform-qa; Due: 2026-03-17** (with lifecycle wording sync follow-through by **release-governance; Due: 2026-03-17**).

Dependency evidence pointer (2026-03-09): `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` with linked behave/pytest logs, reproducible CLI traces, and canonical gate artifacts used for open/blocked pending evidence tracking.
Governance validator fallback audit (2026-03-10): `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` documents `origin/main` unavailability, automatic `HEAD~1` fallback, and explicit `HEAD~1` reruns for auditable readiness evidence.

## Missing evidence checklist (dependency gate)

- [x] **Owner: runtime-pipeline** — Resolved prior failure attribution mismatch in `docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log` and documented corrective note. **Done: 2026-03-09**. Artifact: `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`.
- [x] **Owner: platform-qa** — Re-ran canonical gate (`--continue-on-failure`) and published refreshed failed snapshot artifact (`artifacts/all-green-gate-summary.json`, timestamp `2026-03-10T20:32:23Z`). **Done: 2026-03-10**. Artifact: `artifacts/all-green-gate-summary.json`.
- [x] **Owner: release-governance** — Updated lifecycle language in ISSUE-0013/0014/0015/RED_TAG after refreshed evidence confirmed failed-gate dependency posture (not dependency satisfaction). **Done: 2026-03-10**. Artifact: `artifacts/all-green-gate-summary.json`.

## Resolved

- ISSUE-0007 — **Governance readiness gate traceability is partial for capability-linked issue enforcement**: Closed after deterministic capability-to-issue linkage surfaced in generated feature-status artifacts and validators passed with documented base-ref fallback behavior.
- ISSUE-0001 — **Establish measurable and trackable in-repo issue governance**: Governance is now machine-enforced via canonical validators in the release gate, with auditable failure modes for missing linkage and incomplete issue records.
- ISSUE-0006 — **Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure**: Contributor/test guidance and merge validation now enforce the same governance evidence contract, closing the adoption gap.
- ISSUE-0004 — **BDD policy declared but not executable in repository**: Executable baseline BDD coverage now exists, reducing policy-to-practice drift risk to ongoing contract maintenance.

## Archival notes (non-red lifecycle references)

- ISSUE-0008 was previously listed here during its red-severity phase, but its canonical issue file is now `Severity: amber` and `Status: in_progress`; it is intentionally excluded from active/resolved red-tag tracking.
