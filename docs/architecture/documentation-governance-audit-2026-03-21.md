# Documentation Governance Audit — Structural Honesty (2026-03-21)

## 1. Scope and method

This is a **structural-honesty audit of the documentation system**, not a prose-quality review and not a document inventory.

### Reviewed artifacts (minimum scope + authority/enforcement chain)
Non-Markdown artifacts reviewed in scope:
- `.github/workflows/issue-link-validation.yml`
- `scripts/all_green_gate.py`
- `scripts/architecture_boundary_report.py` (as invoked by gate)
- `tests/architecture/test_import_boundaries.py`

Markdown artifacts reviewed **in scope** (11):
- `plan.md`
- `docs/pivot.md`
- `docs/architecture/plan-execution-checklist.md`
- `docs/architecture/architecture-governance-audit-2026-03-20.md`
- `docs/testing.md`
- `docs/issues.md`
- `docs/issues/governance-control-surface-contract-freeze.md`
- `docs/architecture-boundaries.md`
- `CONTRIBUTING.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/architecture.md`

Markdown artifacts explicitly **out of scope** for this audit pass (96):
- `AGENTS.md`
- `CHANGELOG.md`
- `README.md`
- `artifacts/architecture-boundary-report.current.md`
- `docs/architecture/behavior-governance.md`
- `docs/architecture/canonical-turn-pipeline.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
- `docs/directives/CHANGE_POLICY.md`
- `docs/directives/decision-policy.md`
- `docs/directives/invariants.md`
- `docs/directives/product-principles.md`
- `docs/directives/traceability-matrix.md`
- `docs/governance/architecture-drift-register.md`
- `docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `docs/governance/drift-remediation-backlog.md`
- `docs/governance/drift-traceability-matrix.md`
- `docs/governance/issue-implementation-audit.md`
- `docs/governance/mission-vision-alignment.md`
- `docs/governance/python-code-review-checklist-dependency-boundaries.md`
- `docs/invariants.md`
- `docs/invariants/answer-policy.md`
- `docs/invariants/pipeline.md`
- `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `docs/issues/ISSUE-0003-readme-layout-drift.md`
- `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`
- `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`
- `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `docs/issues/RED_TAG.md`
- `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md`
- `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`
- `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md`
- `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
- `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md`
- `docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md`
- `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md`
- `docs/issues/evidence/governance-stabilization-checklist.md`
- `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
- `docs/issues/evidence/issue-0022-pass-seven-verification-log.md`
- `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `docs/issues/evidence/sprint-00-kpi-review.md`
- `docs/issues/evidence/work-history-assessment-2026-03-17.md`
- `docs/ops.md`
- `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `docs/qa/feature-status-report.md`
- `docs/qa/live-smoke.md`
- `docs/qa/smoke-evidence-contract.md`
- `docs/quickstart.md`
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `docs/style-guide.md`
- `docs/terminology.md`
- `docs/testing-triage.md`
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

### Evidence counted

Evidence counted only where repo behavior is observable, including:

- Whether CI workflows execute a rule.
- Whether `scripts/all_green_gate.py` executes a check and whether it marks it blocking/non-blocking.
- Whether test/config artifacts actually encode the claimed rule.
- Whether PR template or contributor guidance creates mandatory behavior.
- Whether other canonical docs point contributors to a document first.

### What did **not** count as progress evidence

The following were treated as non-evidence by themselves:

- “canonical” or “authoritative” labels in titles/headers,
- additional cross-links or summaries,
- checklists not tied to execution,
- ownership claims not tied to a gate/check.

### Structural-honesty target being tested

This audit explicitly evaluates whether the documentation system currently has:

1. **one canonical statement of intended progress**,
2. **one executable encoding of the enforceable subset**,
3. **and one blocking gate that binds them**.

Current determination: this triad is only partially real; intended progress and enforcement are split across multiple docs, and the only clearly blocking CI workflow is issue-link focused rather than architecture-drift focused.

---

## 2. Executive summary

Today, the file that most nearly acts as canonical intended-progress authority is **`docs/architecture/plan-execution-checklist.md`** (because multiple docs route “what remains” decisions there first), the file that most nearly acts as executable enforcement authority is **`scripts/all_green_gate.py`** (because it is the only artifact that centrally defines blocking vs warning checks), and the currently real merge-blocking CI gate is **`.github/workflows/issue-link-validation.yml` / job `validate-issue-links`** (because it is the only repository workflow shown that executes on pull requests and fails on governance-linkage drift). Architecture-boundary drift is only partially blocked: static import-boundary tests are blocking when run, but the boundary report path is explicitly non-blocking warning mode in the canonical gate.

Net: governance is partially real, partially documentary fiction. The system can answer where to start for progress and where enforcement lives, but it cannot yet claim a single bind between intended architecture progress and a guaranteed PR-blocking drift gate.

---

## 3. Documentation authority table

| Concern | Claimed authority | Observed actual authority | Actual-use evidence | Authority classification | Recommended canonical owner | Action |
| ------- | ----------------- | ------------------------- | ------------------- | ------------------------ | --------------------------- | ------ |
| Intended progress / migration progress | `plan.md`, `docs/pivot.md`, `docs/architecture/plan-execution-checklist.md` all claim planning authority | `docs/architecture/plan-execution-checklist.md` is practical “what is still open” driver | `plan.md` explicitly tells readers to start with checklist first; checklist carries unresolved obligations + do-not-claim-yet language | `canonical` (checklist), `transitional` (pivot), `reference` (plan) | `docs/architecture/plan-execution-checklist.md` | Collapse remaining-open progress assertions in `plan.md`/`docs/pivot.md` to links + deltas only |
| Architecture contract | `docs/architecture/canonical-turn-pipeline.md`, `docs/architecture.md`, `docs/architecture-boundaries.md` | Split between runtime contract doc + executable tests | `docs/architecture-boundaries.md` says enforced by `tests/architecture/test_import_boundaries.py`; gate runs those tests via pytest | `canonical` (pipeline contract), `operational` (boundary test), `reference` (`docs/architecture.md`) | Contract: `docs/architecture/canonical-turn-pipeline.md`; enforceable subset: `tests/architecture/test_import_boundaries.py` | Keep contract prose separate; keep enforceable subset mirrored only where executable |
| PR review standards | `CONTRIBUTING.md`, `docs/testing.md` checklist, PR template | Actual hard requirement in CI is issue-link check; template is advisory text unless validated | `.github/workflows/issue-link-validation.yml` runs issue-link validator on PR; template has Issue placeholder but no direct lint step shown | `operational` (workflow+validator), `reference` (`CONTRIBUTING.md`), `decorative/partial` (template alone) | `.github/workflows/issue-link-validation.yml` + `scripts/validate_issue_links.py` | Convert PR checklist obligations to explicitly “blocking vs advisory” labels in docs |
| Enforcement status declarations | `docs/testing.md`, `docs/architecture/plan-execution-checklist.md`, `docs/pivot.md`, `plan.md` | `scripts/all_green_gate.py` is source of truth for gate check blocking flags | `GateCheck(... blocking=False)` for architecture boundary report; run loop converts failed non-blocking checks to warnings | `canonical` (script), docs mostly `reference/transitional` | `scripts/all_green_gate.py` | Add generated check-matrix artifact as single publication surface; trim duplicated status prose |
| Compatibility declarations | `docs/pivot.md`, architecture audit docs, testing rollout sections | Transitional declarations scattered, some living as standing policy text | Multiple docs describe warning→blocking ratchet, compatibility exceptions, and future enforcement | `transitional` | `docs/architecture/plan-execution-checklist.md` (until closure) | Move time-bounded compatibility declarations into issue records + gate artifact fields |
| Blocking merge criteria | `docs/testing.md` claims canonical gate; CI workflow coverage is narrower | In hosted CI, only visible guaranteed PR workflow is issue-link validation; all_green gate appears policy-canonical but not shown as workflow here | `.github/workflows/issue-link-validation.yml` exists; no workflow file shown that runs `scripts/all_green_gate.py` on PR | `split: operational (issue-link CI), reference/canonical-intent (testing doc)` | `.github/workflows/*` should include a single canonical readiness gate workflow | Add PR workflow invoking `python scripts/all_green_gate.py --profile readiness` |
| Transitional governance mechanism acting as de facto authority | `docs/issues/governance-control-surface-contract-freeze.md` | Freeze doc currently overrides older prose by explicit precedence | `docs/issues.md` freeze notice says freeze doc takes precedence during freeze window | `transitional` (but currently de facto canonical for scoped surfaces) | `docs/issues/governance-control-surface-contract-freeze.md` while active | Add explicit sunset/exit trigger reference in top-level governance navigation |

---

## 4. Document conformity table

| Document | Intended purpose | Actual role in practice | Evidence for actual role | PR-local or transitional content present? | Conformity | Risk classification | Next action |
| -------- | ---------------- | ----------------------- | ------------------------ | ----------------------------------------- | ---------- | ------------------- | ----------- |
| `plan.md` | North-star plan and architecture intent | Meta-navigation + broad strategy + still contains enforcement-status commentary | It tells readers to use checklist first for closure; also duplicates status notes | Yes — contains date-stamped current-status fragments that behave like transitional release notes | Partial | Split-authority drift | Keep north-star only; move “current status” and ratchet notes to checklist/issues |
| `docs/pivot.md` | Migration map + scored extraction priorities | Transitional migration ledger and partial enforcement roadmap | Contains scored census + remaining deliverables + planned verification hooks | Yes — PR/migration-phase specifics and staged rollout policy | Partial | Overextended transitional authority | Keep as migration reference; strip “enforcement should” statements once encoded in gate |
| `docs/architecture/plan-execution-checklist.md` | Unresolved obligations + closure contract | De facto primary progress authority | Other docs route to it first; has done-signal language and do-not-claim-yet controls | Yes — includes dated progress notes and ratchet state | High | Manageable if treated as single progress ledger | Promote explicitly as sole intended-progress authority until closure |
| `docs/architecture/architecture-governance-audit-2026-03-20.md` | Prior structural audit | Historical evidence snapshot | Date-specific PR verdicts and one-time findings | Yes — PR-specific determinations | High for historical role | Low (if not mistaken as live authority) | Keep historical; add pointer to latest audit in header if needed |
| `docs/testing.md` | Canonical testing/readiness guidance | Mixed canonical + policy expansion + PR runbook storage | Defines canonical gate and architecture boundary rollout status; includes extensive governance policy text | Yes — includes runbook/checklist material that can become PR-local | Partial | Governance fan-out | Keep command contract canonical; relocate PR recovery/checklist details to contributor workflow docs or issue templates |
| `docs/issues.md` | Canonical issue workflow | Operational policy source for issue schema + validators | Validator commands and schema expectations align with CI/workflow usage | Yes — freeze-precedence note introduces temporary override | High (with active override) | Freeze-induced split authority | Keep stable core schema here; keep temporary precedence bounded and time-boxed |
| `docs/issues/governance-control-surface-contract-freeze.md` | Temporary stabilization contract | Active override authority for coupled control surfaces | Explicit precedence clause in `docs/issues.md` | Entirely transitional by design | Conformant for temporary role | If freeze lingers, permanent governance bifurcation | Add explicit lift criteria owner + target review date linkage in primary nav |
| `.github/PULL_REQUEST_TEMPLATE.md` | Guide PR authors | Advisory reminder only | No direct enforcement artifact consumes template fields in reviewed scope | Yes — metadata prompts belong to PR-local context | Conformant (advisory) | Decorative if treated as governance authority | Keep minimal; avoid carrying policy that isn’t validated |
| `.github/workflows/issue-link-validation.yml` | PR governance enforcement | Actual blocking PR check for issue linkage | Runs on `pull_request`, executes validator | No | High | Narrow-scope enforcement only | Add/readiness workflow for full drift blocking |

Decision test (“if file disappeared tomorrow, what breaks?”) summary:
- Breaks actual merge checks: workflow file + validator script + gate script.
- Breaks planning coordination but not merge: checklist/plan/pivot docs.
- Breaks little directly: PR template alone.

---

## 5. Governance claim enforcement table

| Governance claim | Source document | Enforcement mechanism | Enforcement status | Blocking? | Evidence | Gap type | Required remediation |
| ---------------- | --------------- | --------------------- | ------------------ | --------- | -------- | -------- | -------------------- |
| “Issue linkage is mandatory for non-trivial changes” | `CONTRIBUTING.md`, `docs/issues.md`, PR template | `scripts/validate_issue_links.py` run in `.github/workflows/issue-link-validation.yml` and in readiness gate profile | `blocking` | yes | PR workflow job `validate-issue-links`; gate includes `qa_validate_issue_links` in readiness profile | Scope gap (only this governance slice in CI workflow) | Keep; integrate with broader readiness workflow |
| “Canonical merge/readiness gate is `all_green_gate`” | `docs/testing.md`, AGENTS guidance | `scripts/all_green_gate.py` check runner | `partial` | no (at PR workflow level not evidenced) | Script defines checks and blocking semantics, but no reviewed PR workflow invokes it | CI binding gap | Add GitHub workflow running readiness profile on PR |
| “Architecture boundary findings are enforced” | `docs/testing.md`, `docs/architecture/plan-execution-checklist.md` | `qa_architecture_boundary_report` in gate + import-boundary pytest | `partial` | report: no; static import tests: yes (when executed) | Gate sets boundary report `blocking=False`; run loop downgrades failed non-blocking to warning; separate blocking import-boundary tests exist via pytest | Mixed-mode ambiguity | Publish explicit matrix: which boundary controls are blocking now vs warning |
| “Boundary report is in warning mode pending promotion” | `docs/testing.md` | `scripts/all_green_gate.py` configuration | `blocking` (as statement about non-blocking mode itself) | yes (for truth of mode), no (for violations) | Gate code hard-codes `qa_architecture_boundary_report` non-blocking | Deferred-enforcement debt | Promote to blocking once criteria met, then remove duplicate caveats across docs |
| “KPI guardrail checks are mode-controlled” | `docs/testing.md` | Gate mode flag `--kpi-guardrail-mode` toggles blocking | `partial` | depends on mode | Gate sets `kpi_blocking = (mode == "blocking")` | Operational optionality drift | Keep optional but expose active mode in CI check name/artifact |
| “Do not over-claim workstream completion” | `docs/architecture/plan-execution-checklist.md` | None direct (documentation discipline only) | `documented-only` | no | “Do-not-claim-yet” bullets have no dedicated linter/check | Claim drift risk | Add small policy validator (or manifest rule IDs) for completion claims |
| “Freeze document is normative during stabilization window” | `docs/issues.md` + freeze doc | Human-governed precedence, no dedicated freeze-status check observed | `documented-only` | no | Explicit precedence statement exists; no automated freeze-lift/expiry check found | Transitional lock-in risk | Add date/issue-based automated expiry assertion in governance validators |
| “PR template Issue field enforces issue reference” | `.github/PULL_REQUEST_TEMPLATE.md` | None by template itself | `obsolete` as enforcement mechanism | no | Template only provides placeholder text | False-authority risk | Keep template as UX aid; never cite it as enforcement evidence |

---

## 6. Documentation duplication / split-authority table

| Topic | Documents that mention it | Why this is split authority | Which document should own it | What the others should do instead |
| ----- | ------------------------- | --------------------------- | ---------------------------- | --------------------------------- |
| Intended progress | `plan.md`, `docs/pivot.md`, `docs/architecture/plan-execution-checklist.md` | Multiple “status” narratives with different granularity | `docs/architecture/plan-execution-checklist.md` | `plan.md` = long-range intent only; `docs/pivot.md` = migration mechanics only |
| Current migration status | `docs/pivot.md`, checklist, architecture audit (2026-03-20), parts of `plan.md` | Time-stamped status duplicated in permanent docs | Checklist (active), issue records (evidence) | Older audits stay historical; remove live-status language from older docs |
| Architecture rules | `docs/architecture-boundaries.md`, `docs/testing.md`, `plan.md`, `docs/pivot.md` | Rule definitions and rollout status repeated | Executable tests + gate config as source; `docs/architecture-boundaries.md` as prose mirror | Other docs link out; avoid restating rule text |
| Enforcement status | `docs/testing.md`, checklist, pivot, plan | Blocking vs warning semantics repeated across docs | `scripts/all_green_gate.py` (generated matrix) | Docs reference generated matrix snapshot |
| Compatibility declarations | `docs/pivot.md`, checklist, testing rollout, audits | Temporary compatibility treated as semi-permanent prose policy | Issue records + boundary report artifact classifications | Docs describe policy once; specifics live in artifacts/issues |
| Review/gate criteria | `docs/testing.md`, `CONTRIBUTING.md`, PR template, workflow file | Advisory checklist and actual blocking checks not clearly separated | CI workflow + gate script | Contributor docs explicitly map each item to blocking/non-blocking artifact |

---

## 7. Transitional or PR-local content embedded in permanent docs

| File | Section | Transitional / PR-local content | Why it does not belong here | Better home | Required action |
| ---- | ------- | ------------------------------- | --------------------------- | ----------- | --------------- |
| `docs/testing.md` | “Runbook: conflicted PR recovery (PR #78-class re-qualification)” | PR conflict-recovery procedural checklist and PR-body evidence instructions | PR-event specific workflow guidance, not stable product/test contract | `CONTRIBUTING.md` or dedicated short PR-runbook doc linked from template | Relocate runbook; keep `docs/testing.md` focused on canonical gate semantics |
| `plan.md` | Date-stamped “Current status (2026-03-19)” enforcement notes | Transitional checkpoint commentary embedded in long-range architecture plan | Causes live-status authority fan-out against checklist | `docs/architecture/plan-execution-checklist.md` + linked issue | Remove/condense status notes into pointers to checklist/issues |
| `docs/pivot.md` | “Concrete deliverables for next PRs” with issue slices and immediate slice notes | PR-slice planning and in-flight migration declarations | Time-bounded execution tracking, not durable architecture map | Issue records (`docs/issues/ISSUE-0013*`) + checklist | Keep only durable migration model; move in-flight slice state out |
| `docs/issues/governance-control-surface-contract-freeze.md` | Freeze precedence over broad control surfaces | Temporary override with wide blast radius in permanent docs tree | Necessary now but should not become standing dual-authority regime | Time-boxed issue + validator-enforced expiry | Add explicit automated expiry/lift check and retire once reconciled |
| `docs/architecture/architecture-governance-audit-2026-03-20.md` | PR-specific do-not-merge table | Snapshot judgments about specific PRs | Historical evidence, not present governance authority | Historical archive section | Mark clearly as historical snapshot with “superseded by latest audit” pointer |

---

## 8. Final synthesis

1. **Canonical intended-progress file (current/should be explicit):**
   - `docs/architecture/plan-execution-checklist.md`

2. **Executable enforcement artifact (current):**
   - `scripts/all_green_gate.py` (check registry + blocking semantics)
   - with architecture subset enforcement in `tests/architecture/test_import_boundaries.py`

3. **Blocking gate (current real behavior):**
   - `.github/workflows/issue-link-validation.yml` job `validate-issue-links` is the only clearly evidenced PR-blocking workflow.
   - A full drift-blocking gate binding docs↔reality for architecture/governance remains unresolved until PR CI runs `python scripts/all_green_gate.py --profile readiness`.

If the program intends to claim “documentation and repo reality divergence is blocked,” that claim is currently unresolved governance, not yet a fully realized control.

### Earliest signs of documentation collapse

- One concept (progress/enforcement status) spread across `plan.md`, `docs/pivot.md`, checklist, testing policy, and dated audits.
- Permanent docs storing transitional declarations and PR-era rollout notes.
- Checklists declaring obligations without a one-to-one mapping to a blocking check ID.
- Mixed messaging where architecture enforcement is described as canonical while boundary-report violations are still warning-only.
- Temporary freeze authority living alongside canonical workflow docs, creating deliberate but risky dual authority.

### Where governance is real vs still fiction

**Real**
- Issue-link governance is executable and PR-blocking in CI.
- Gate script centrally encodes blocking vs warning semantics.
- Static import-boundary checks exist as executable tests.

**Still fiction / partial**
- Single PR-blocking “all_green readiness” workflow is not evidenced.
- Architecture boundary report exists but is explicitly non-blocking.
- Documentation claims about closure/completion often rely on prose checkpoints not machine-enforced claim controls.

### Minimal remediation sequence

1. **Bind blocking gate to CI reality:** add one PR workflow invoking `python scripts/all_green_gate.py --profile readiness`.
2. **Publish one enforcement matrix from code:** generate and reference a check-status artifact directly from `scripts/all_green_gate.py` (blocking/warning/skipped semantics), then remove duplicated status prose across docs.
3. **Consolidate intended progress:** keep unresolved obligations only in `docs/architecture/plan-execution-checklist.md`; convert `plan.md` and `docs/pivot.md` status text to links.
4. **Move PR-local/transitional material out of permanent policy docs:** relocate conflicted-PR runbook and in-flight slice notes to issue/PR metadata or time-bounded runbooks.
5. **Time-box freeze authority:** add validator-backed expiry/lift requirement for `docs/issues/governance-control-surface-contract-freeze.md` to prevent permanent split governance.

