# Testing

## Who
Developers and QA contributors validating behavior, scoring logic, and integration wiring.

## What
A layered test strategy: BDD for stakeholder-visible behavior, deterministic unit/component tests for logic, and optional live smoke checks for environment confidence.

## When
- **BDD (`behave`)**: before/with any user-visible behavior change and before merge.
- **Unit/component (`pytest`)**: during implementation and in default local/CI runs.
- **Live smoke**: after infra or deployment-relevant changes, run separately from default fast suites.

## Where
From the repository root with project dependencies installed. Prefer offline deterministic runs by default; only live smoke tests should require Home Assistant/Ollama connectivity.

## Why
This split keeps acceptance behavior explicit, speeds feedback loops, and avoids flaky default suites while still providing optional end-to-end confidence.

Program anchor: [`issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).

## BDD-first policy

Behavior that stakeholders care about must be written first as `.feature` scenarios. Implementation is complete only when those scenarios pass and deterministic supporting tests confirm lower-level logic.

## Canonical Turn Pipeline TDD

Use this section as the required test-first blueprint for pipeline work aligned to the canonical stage sequence in [`docs/architecture/canonical-turn-pipeline.md`](architecture/canonical-turn-pipeline.md).

### Test-first order by stage

Write tests in pipeline order before implementation changes, then make each stage green without skipping upstream stage failures:

1. `observe.turn` + `encode.candidates`: observation preservation and multiplicity capture tests.
2. `stabilize.pre_route` + `context.resolve`: durable pre-route facts/provenance and pending-repair/context anchor tests.
3. `intent.resolve`: resolved-intent authority and telemetry alias consistency tests.
4. `retrieve.evidence`: retrieval branch coherence and empty-evidence distinction tests.
5. `policy.decide`: action-class choice determinism and ambiguity handling tests.
6. `answer.assemble` + `answer.validate`: provenance binding, grounding, and decision/answer-class alignment tests.
7. `answer.render` + `answer.commit`: render-class preservation and committed-state persistence tests.

Validation-failure answer contract (canonical):
- Normal render/commit paths require `answer.validate.passed == True`.
- If validation fails, canonical execution may only produce/commit an explicit degraded artifact (`[degraded:clarifier]`, `[degraded:alternatives]`, or `[degraded:deny]`).
- Unvalidated semantic answer text must never be rendered or committed as a normal answer.

### Required test categories per stage set

Every stage-affecting change must include all three categories below:

- **Stage contract tests**: deterministic checks that the stage input/output and stage invariants hold.
- **Decision matrix tests**: matrix-style scenario checks proving stable branch selection across intent, evidence, capability, and ambiguity combinations.
- **Property/regression tests**: invariant-preserving property checks and explicit regressions for previously observed failure modes.

Any missing category is a readiness failure even when individual spot checks pass.

### Fake adapter strategy (deterministic by default)

Prefer fake adapters for pipeline tests unless a test is explicitly marked live smoke:

- Replace LLM/rewrite/answer generators with deterministic fakes or fixtures.
- Replace vector stores/connectors with in-memory fakes and fixed timestamps.
- Keep provenance IDs, candidate ordering, and fallback actions deterministic.
- Use monkeypatch or dependency injection at runtime boundaries instead of network calls.

This strategy is required to keep stage contracts, decision matrix coverage, and regressions reproducible under `python scripts/all_green_gate.py`.

## Scenario traceability quick map

For fast failure triage across behavior specs, runtime anchors, and deterministic tests, use [docs/directives/traceability-matrix.md](directives/traceability-matrix.md#quick-reference-fast-triage).

## Test layers

### 1) BDD scenarios (`behave`)

Use BDD to validate externally visible outcomes:

- Memory-grounded responses include `doc_id` and `ts` when context is sufficient.
- Assistant uses progressive fallback when memory is insufficient: ask one targeted clarifier or offer at least two capability-based alternatives; reserve exact `I don't know from memory.` for explicit deny/safety-only cases.
- Time-aware retrieval behavior matches expected outcomes for representative phrasing.

`behave` is mandatory for canonical merge validation. If `behave` is missing, your environment is not ready; use the canonical remediation in [BDD tooling health check (canonical)](#bdd-tooling-health-check-canonical).

Recommended layout:

```text
features/
├─ memory_recall.feature
├─ answer_contract.feature
└─ steps/
   ├─ memory_steps.py
   └─ answer_contract_steps.py
```

### 2) Pure unit tests (`pytest`)

Validate deterministic core logic with no model/network dependencies:

- Time parsing and target-time inference
- Sigma adaptation and Gaussian weight computation
- Rerank score composition and ordering

### 3) Component tests with fakes (`pytest`)

Test retrieval/answer pipeline wiring with deterministic stubs:

- Stub rewrite/answer outputs
- Use deterministic fake embeddings and in-memory stores
- Assert stable top-k ordering and progressive fallback behavior (clarifier/alternatives for insufficient memory; exact fallback only for deny/safety-only cases).

### Source-ingestion failure-mode checks (offline, fake-backed)

For source-ingestion reliability checks, prefer monkeypatches/fakes over any live connector or backend:

- Simulate connector fetch failures (for example, `HTTPError`) and assert startup continues while `source_ingest_failed` is logged.
- Simulate memory-store `add_documents` failures (for example, embedding/backend outage) and assert failure logging plus non-fatal startup behavior at runtime boundary tests.
- In `SourceIngestor` unit tests, use fake stores/connectors and assert `add_documents` exceptions propagate so the runtime layer can apply the non-fatal handling contract.

These tests are deterministic and do **not** require production Ollama, Home Assistant, or any network connectivity.


### 4) Optional live integration smoke tests

Run separately against real Home Assistant + Ollama for environment confidence. Keep these tests opt-in and out of default quick runs.

Live-smoke suites are expected to self-skip when required environment variables are missing. Skip notices should explicitly state both **why** execution was skipped (which variables are absent) and the **expected behavior** once configuration is provided (end-to-end checks run against reachable live services).

## Commands

Use the following canonical commands from repository root.

### Quick contributor validation

For non-live changes, this is the expected offline/deterministic contributor gate:

1. `pip install -e .[dev]`
2. `python scripts/all_green_gate.py`

`pip install -e .[dev]` is the canonical contributor install command and includes runtime dependencies plus development/validation tooling.

`scripts/all_green_gate.py` is the only authoritative command sequence for merge readiness. It now supports explicit staged profiles:

- `triage`: runtime correctness + schema + core deterministic tests (default for local contributor runs).
- `readiness`: full merge/release obligations, including governance validators and KPI rollups (default in CI/release environments).

BDD execution is a hard prerequisite for interpreting feature-status evidence as behavior confidence; if BDD cannot run, treat capability status as not confidence-ready until `behave` is restored via `pip install -e .[dev]`.

Default behavior is fail-closed (stop on first failure). Use `--continue-on-failure` to run every check and still exit non-zero if any check fails.

### Turn analytics input semantics and coverage diagnostics

`python scripts/aggregate_turn_analytics.py` consumes session JSONL rows with mixed runtime events, but only the analytics event vocabulary participates in turn construction:

- `user_utterance_ingest` (required turn starter)
- `intent_classified`
- `fallback_action_selected`
- `provenance_summary`

All other event classes are retained as input but treated as non-analytics rows for turn aggregation. The generated summary (`logs/turn_analytics_summary.json` by default) includes deterministic coverage diagnostics so operators can interpret utilization explicitly:

- `input_rows_total`
- `recognized_analytics_rows`
- `ignored_non_analytics_rows`
- `turn_start_events`
- `ignored_event_counts`
- `warnings`

Warning policy is deterministic and emitted in both CLI output (`WARNING: ...` on stderr) and serialized summary metadata:

- Warn when `ignored_non_analytics_rows / input_rows_total > 0.5`
- Warn when `input_rows_total > 0` and `turn_start_events == 0`

These diagnostics are intended to make semantic coverage explicit, especially for high-volume runtime/process events (for example `pipeline_state_snapshot`, `stage_transition_validation`) that do not start or enrich turns.

### Turn analytics in canonical gate

The canonical gate (`scripts/all_green_gate.py`) supports KPI rollout controls via `--kpi-guardrail-mode {off,optional,blocking}` (default: `optional`). In `optional`, `scripts/aggregate_turn_analytics.py` and `scripts/validate_kpi_guardrails.py` run as non-blocking warnings; in `blocking`, the same failures block gate success; in `off`, both checks are skipped.

#### KPI guardrail mode policy (authoritative)

Allowed values for `--kpi-guardrail-mode` are fixed to:

- `off`: skip turn analytics aggregation and KPI guardrail validation checks.
- `optional` (default): run KPI checks as warning-only signals that do not fail the canonical gate.
- `blocking`: run KPI checks as required checks that fail the canonical gate on guardrail violations.

Default mode rationale (`optional`): KPI guardrails are still being operationalized as release-governance telemetry, so the repository keeps them visible in every canonical gate run without allowing KPI threshold drift to silently disappear. This preserves deterministic warning visibility while the team accumulates sufficient sprint evidence to justify promotion.

Promotion criteria from `optional` to `blocking` (all required):

1. Two consecutive sprint KPI evidence reviews (`docs/issues/evidence/sprint-<NN>-kpi-review.md`) show zero guardrail violations against `config/kpi_guardrails.json`.
2. The same two-sprint window has no unresolved KPI warning entries in `artifacts/all-green-gate-summary.json` for `qa_validate_kpi_guardrails`.
3. `docs/issues/RED_TAG.md` triage updates confirm no open blocker/dependent issue is carrying forward unresolved KPI warning debt.
4. Promotion is documented in issue governance metadata (linked issue record + decision note) before changing automation defaults.

Severity/state interpretation for warning-mode KPI results:

- **Accepted debt**: non-red issues (`Severity: amber`/`green`) may carry KPI warnings while status remains `in_progress`/`open`, but each warning cycle must include explicit issue linkage (issue ID, owner, due date, mitigation note).
- **Blocker**: red-severity issues (`Severity: red`) or any issue in a declared blocker/dependent closure path must treat persistent KPI warnings as blocker evidence until linked mitigation and closure dates are recorded.
- **Not allowed**: marking an issue `resolved`/`closed` while unresolved KPI warnings persist without linked mitigation issue evidence.

When KPI warnings persist in `optional` mode, repository policy requires issue linkage in all three locations for each review cycle: the canonical issue record decision note, `docs/issues/RED_TAG.md` triage note (when red-tagged), and the sprint KPI evidence note.

## Architecture boundary report mode policy (authoritative)

Current mode: `warning` in the canonical readiness gate.
The architecture boundary report runs during `python scripts/all_green_gate.py --profile readiness` and is surfaced as readiness evidence. Boundary-report findings do not currently fail the gate by themselves. Blocking checks such as `product_behave` and `qa_pytest_not_live_smoke` remain fail-closed and continue to determine gate failure.

The architecture boundary report rollout supports exactly three modes:

- `report_only`
- `warning`
- `blocking`

### 1. Scope

The architecture boundary report covers these architectural areas:

- `entrypoints`
- `application`
- `logic`
- `domain`
- `ports`
- `adapters`
- `observability`

Its purpose is to detect architectural drift in placement and dependency direction during the ongoing extraction/hardening phase.

### 2. Classification contract

Architecture boundary report results are classified as:

- `violation`: boundary break not currently sanctioned.
- `temporary_exception`: known temporary boundary break allowed during migration.
- `deprecated_compatibility`: compatibility/deprecation surface intentionally retained during retirement window.
- `allowed`: conforms to current boundary policy.

`temporary_exception` and `deprecated_compatibility` are not equivalent to `allowed`, and both classes must remain visible in readiness evidence.

Temporary compatibility exceptions are allowed only when issue-linked. An unlinked temporary exception must be treated as a violation for governance purposes, even if the boundary report remains non-blocking in the current rollout mode.

### 3. Current gate behavior

Current rollout behavior is fixed as follows:

- The architecture boundary report runs in the readiness gate (`python scripts/all_green_gate.py --profile readiness`).
- The check is surfaced in gate output and in the JSON summary.
- Boundary findings currently produce a non-blocking warning outcome.
- The gate still exits non-zero on blocking-check failures.
- The architecture report does not override, suppress, or replace existing deprecated alias enforcement.

### 4. Promotion criteria to blocking

Promotion from `warning` to `blocking` is allowed only when all of the following are true:

1. Two consecutive readiness-gate runs in the intended validation environment show:

   - zero unsanctioned `violation` findings,
   - and no increase in `temporary_exception` count.
2. Every `temporary_exception` is linked to:

   - an issue ID,
   - an owning module/package,
   - a stated removal target or review date.
3. No new business logic has landed in `sat_chatbot_memory_v2.py` except:

   - compatibility delegators,
   - warning/deprecation metadata,
   - or migration-only adapter glue explicitly tracked as temporary.
4. Existing deprecated alias enforcement remains green.
5. Promotion is recorded in repo governance artifacts before the default gate mode is changed.

| Test layer | Canonical command | Runtime dependency | CI gate level | Expected runtime | Pass criteria |
| --- | --- | --- | --- | --- | --- |
| Local triage gate (default local profile) | `python scripts/all_green_gate.py` | Python dev extras (`behave`, `pytest`) plus local fixtures | **Required for local iteration** | ~20-90s depending on test volume | Exit code `0`; runtime correctness + schema + core deterministic checks pass (BDD, recall eval, log/schema + pipeline-stage conformance, deterministic `pytest -m "not live_smoke"`). |
| Merge/readiness gate (full profile) | `python scripts/all_green_gate.py --profile readiness` | Python dev extras (`behave`, `pytest`) plus local docs/issues/fixtures and git metadata | **Required (canonical merge/release gate)** | ~30-150s depending on test volume | Exit code `0`; all triage checks plus governance/invariant/markdown-path validators and KPI guardrail checks (mode-dependent) pass. **Interpret feature-status evidence as behavior confidence only when this gate includes a successful BDD run.** |
| BDD acceptance (`behave`) | `python -m behave` _(requires `pip install -e .[dev]` first)_ | Python dev extras (`behave`) and local deterministic fixtures | **Executed by canonical gate (component check)** | ~10-60s for current feature set | Exit code `0`; no failed/undefined steps; acceptance scenarios for changed behavior pass. |
| Deterministic unit/component (`pytest`) | `python -m pytest -m "not live_smoke"` | Python dev extras (`pytest`); no network or external services | **Executed by canonical gate (component check)** | ~5-30s for fast deterministic scope | Exit code `0`; no flaky network-bound failures; logic and wiring tests for changed code pass. |
| Eval/runtime parity check (`pytest`) | `python -m pytest tests/test_eval_runtime_parity.py` | Python dev extras (`pytest`) and fixed fixtures (`eval/cases.jsonl`, `tests/fixtures/candidate_sets.jsonl`) | **Targeted diagnostic check (run manually when parity drift is suspected)** | ~1-5s | Exit code `0`; runtime path scoring and eval adapter path stay aligned for ordering, top-1, and fallback intent decisions. |
| Governance / issue linkage checks | `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` | Local git metadata + docs/issues files | **Executed by canonical gate (component check)** | ~1-5s | Exit code `0`; non-trivial PR/commit metadata include `ISSUE-XXXX`; canonical fields are non-placeholder; required issue section bodies are non-empty; red-severity ownership/sprint/status and RED_TAG consistency checks pass. |
| Policy compatibility checks | `python scripts/validate_issues.py --all-issue-files --base-ref origin/main` | Local git metadata + docs/issues files | **Executed by canonical gate (component check)** | ~1-5s | Exit code `0`; compatibility validator reports no missing canonical sections and no red-tag owner/sprint gaps. |
| Optional live smoke profile | `pytest -m live_smoke` | Reachable Home Assistant + Ollama endpoints and any required env vars/secrets | **Optional (post-merge/manual gate)** | ~1-5 min depending on services | Exit code `0`; no infra/auth/connectivity errors; end-to-end smoke assertions pass. |


### BDD tooling health check (canonical)

If `behave` is missing, your setup is incomplete.

Fix contributor environments with:

```bash
pip install -e .[dev]
```

Do not treat missing `behave` as an acceptable skip for canonical validation.

### Dependency policy for test tooling

- `behave` and `pytest` are **development/test dependencies**, not runtime dependencies of the `testbot` application process.
- Keep them in the `dev` extra (`pip install -e .[dev]`) so production installs stay minimal while merge gates remain enforceable.
- Canonical gate commands should invoke test tools through the active interpreter (`python -m behave`, `python -m pytest`) to reduce PATH-related false failures.

### Canonical command snippets

Run local triage gate (default local profile):

```bash
python scripts/all_green_gate.py
```

Run full merge/release readiness gate:

```bash
python scripts/all_green_gate.py --profile readiness
```

Run gate in run-all mode (returns non-zero if any check failed):

```bash
python scripts/all_green_gate.py --continue-on-failure
```

Write gate results to a JSON artifact (for CI/log processing):

```bash
python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json
```


Run invariant mirror sync (writes updates to `docs/directives/invariants.md`):

```bash
python scripts/sync_invariants_mirror.py
```

Validate invariant mirror sync only (non-zero on mismatch):

```bash
python scripts/sync_invariants_mirror.py --check
```


Run pipeline stage conformance validator directly:

```bash
python scripts/validate_pipeline_stage_conformance.py
```

This validator also enforces ontology separation for pipeline-semantics artifacts: stage-semantics rows in `docs/directives/traceability-matrix.md` and section rows in `docs/invariants/pipeline.md` must include at least one `PINV-*` reference, cannot rely solely on response-policy `INV-*` IDs, and may only mix `PINV-*` + `INV-*` when downstream answer-policy consequences are explicitly stated.

Run BDD scenarios directly (requires canonical contributor install `pip install -e .[dev]` first):

```bash
python -m behave
```

Run deterministic unit/component tests only:

```bash
python -m pytest -m "not live_smoke"
```

Run deterministic eval/runtime parity gate:

```bash
python -m pytest tests/test_eval_runtime_parity.py
```

Run optional live smoke profile:

```bash
python -m pytest -m live_smoke
```

Run Ollama live smoke integration tests only (`tests/test_live_smoke_ollama.py`):

```bash
OLLAMA_BASE_URL=http://localhost:11434 \
OLLAMA_MODEL=llama3.1:latest \
OLLAMA_EMBEDDING_MODEL=nomic-embed-text \
X_OLLAMA_KEY=<ollama-api-key> \
python -m pytest tests/test_live_smoke_ollama.py -m live_smoke -vv
```

Expected outcomes for `tests/test_live_smoke_ollama.py`:

- Live smoke modules now gate on required runtime endpoint/model configuration fields being defined and non-empty.
- If prerequisites are set and Ollama is reachable with both models pulled, both tests pass.
- If `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_EMBEDDING_MODEL`, or `X_OLLAMA_KEY` are missing, tests skip with explicit guidance naming the missing variable.
- If endpoint/model provisioning is incorrect, tests fail with a live connectivity/model error (intentional signal that environment is not ready).


Run degraded-mode live smoke scenarios only (`tests/test_live_smoke_degraded_modes.py`):

```bash
# Scenario matrix exercised by this module:
# 1) HA unavailable + Ollama available
# 2) HA available + Ollama unavailable
# 3) both unavailable
#
# Required baseline live env vars:
# - OLLAMA_BASE_URL / OLLAMA_MODEL / OLLAMA_EMBEDDING_MODEL / X_OLLAMA_KEY (for the "Ollama available" scenario)
# - HA_API_URL / HA_API_SECRET / HA_SATELLITE_ENTITY_ID (for the "HA available" scenario)
#
# Failure injection for degraded scenarios is environment-driven only. The test module
# swaps endpoints to unreachable localhost ports (HA: 127.0.0.1:9, Ollama: 127.0.0.1:1)
# and does not monkeypatch runtime connectivity helpers.
OLLAMA_BASE_URL=http://localhost:11434 \
OLLAMA_MODEL=llama3.1:latest \
OLLAMA_EMBEDDING_MODEL=nomic-embed-text \
X_OLLAMA_KEY=<ollama-api-key> \
HA_API_URL=http://localhost:8123 \
HA_API_SECRET=<token> \
HA_SATELLITE_ENTITY_ID=assist_satellite.kitchen \
python -m pytest tests/test_live_smoke_degraded_modes.py -m live_smoke -vv
```

Expected outcomes for `tests/test_live_smoke_degraded_modes.py`:

- Scenario assertions validate effective mode resolution against availability combinations.
- Runtime capability flags (`ha_available`, `ollama_available`) remain internally consistent with startup output.
- User-visible capability guidance remains stable across degraded paths (for example, `CLI fallback is active` and degraded Home Assistant guidance strings).

### Production validation record (live Ollama smoke)

Observed external validation run:

```text
(base) sebastian@grape:~/Services/TestBot$ pytest tests/test_live_smoke_ollama.py
==================== test session starts =====================
platform linux -- Python 3.13.9, pytest-9.0.2, pluggy-1.5.0
rootdir: /home/sebastian/Services/TestBot                     configfile: pyproject.toml
plugins: langsmith-0.6.1, anyio-4.12.0, cov-7.0.0
collected 2 items
tests/test_live_smoke_ollama.py ..                     [100%]

===================== 2 passed in 1.75s =====================
```

### Debug diagnostics for calibration (threshold tuning)

When `TESTBOT_DEBUG=1` is enabled, turn traces include calibration-oriented reject diagnostics under `debug.policy`.
These diagnostics are observability-only and do **not** change routing/answer decisions.

For rejected turns, inspect:

- `rejected_turn`: deterministic reject flag.
- `nearest_failure_gate`: gate name, current value, required value, and `margin_to_pass`.
- `debug.contract.general_knowledge_contract_applicability`: `applicable` vs `not_applicable` contract status.
- `debug.contract.general_knowledge_contract_failed_when_applicable`: alertable boolean (`true` only when applicability is `applicable` and validation failed).
- `counterfactuals.top_candidate_pass_thresholds`: threshold values where the current top candidate would satisfy the score/margin gates.
- `counterfactuals.alternate_routing_policy_checks`: whether alternate routes (for example clarify/route-to-ask) would pass policy checks for the same state.

Recommended workflow for safe tuning:

1. Run canonical gate first: `python scripts/all_green_gate.py`.
2. Reproduce representative debug traces with fixed fixtures (BDD + deterministic pytest).
3. Use `nearest_failure_gate.margin_to_pass` and counterfactuals to propose threshold adjustments.
4. Re-run full gate and confirm no regressions in guardrail-directed scenarios.

Do not use counterfactual diagnostics to bypass contract checks or weaken required grounding/safety outcomes.

Run governance and issue-linkage checks:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
```

Canonical base-ref policy for governance validation in this repository:

- Default `--base-ref` is `origin/main`.
- If `origin/main` is unavailable, first attempt optional recovery to `refs/codex/origin-main` when `ALLOW_REMOTE_BASE_REF_RECOVERY=true` and `GIT_ORIGIN_URL` is configured.
- If recovery is unavailable, fall back in order to `HEAD~1`, then `HEAD`.
- Validators emit explanatory warnings for recovery/fallback mode clarifying Codex task container/shallow-clone expectations and that authoritative diffs require `git fetch origin main` locally.
- This recovery/fallback behavior is by design (contracted), and the gate emits a note when non-default resolution is used.
- You can still override explicitly with `--base-ref <ref>` when validating against a different branch point.

## Runbook: conflicted PR recovery (PR #78-class re-qualification)

Use this runbook when a PR has merge conflicts and must be re-qualified after a rebase.

### Step 1: Rebase and resolve conflicts

```bash
git fetch origin
git rebase origin/main
```

Resolve conflicts, then continue:

```bash
git add <resolved-files>
git rebase --continue
```

### Step 2: Run the canonical full readiness gate

```bash
python scripts/all_green_gate.py --profile readiness --json-output artifacts/all-green-gate-summary.json
```

### Step 3: Run stakeholder-obligation checks explicitly

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
```

If `origin/main` is not present locally (common in shallow CI clones), follow the canonical policy (optional recovery to `refs/codex/origin-main` when enabled, otherwise fallback to `HEAD~1` then `HEAD`) or fetch explicitly:

```bash
git fetch origin main
# or
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1
python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1
```

### Step 4: Record evidence artifact paths in PR body

Add an "Evidence" section to the PR body with exact artifact paths from the re-qualification run.

Required evidence files:

- `artifacts/all-green-gate-summary.json`
- `artifacts/conflicted-pr-recovery/validate-issue-links.txt`
- `artifacts/conflicted-pr-recovery/validate-issues.txt`

Recommended command pattern to capture evidence logs:

```bash
mkdir -p artifacts/conflicted-pr-recovery
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main | tee artifacts/conflicted-pr-recovery/validate-issue-links.txt
python scripts/validate_issues.py --all-issue-files --base-ref origin/main | tee artifacts/conflicted-pr-recovery/validate-issues.txt
```

### Explicit pass criteria (must all be true)

1. Rebase completes with no remaining conflict markers and branch is linear on top of `origin/main` when available.
2. `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json` exits `0`.
3. Governance validators exit `0` under canonical base-ref policy (`origin/main` default; optional recovery to `refs/codex/origin-main` when enabled; fallback `HEAD~1` then `HEAD` when unavailable).
4. PR body contains evidence artifact paths and references the run generated after conflict resolution.


## Readiness evidence (all-systems-green criteria)

The canonical merge-readiness definition of **"all systems green"** is the stakeholder obligations matrix in this document.

Use the matrix as the authoritative map from stakeholder obligations to required deterministic evidence.


### Obligation-to-evidence matrix

| Stakeholder domain | Obligation | Concrete artifacts | Deterministic checks (must pass) |
| --- | --- | --- | --- |
| **Product** | Utility behavior scenarios remain user-trustworthy (memory-grounded answers when evidence exists, progressive clarify/assist fallback when it does not, intent-grounded non-memory responses with explicit basis). | `features/testbot/memory_recall.feature`, `features/testbot/answer_contract.feature`, `features/testbot/intent_grounding.feature`, step harnesses under `features/steps/`. | `python -m behave`; `python -m pytest tests/test_eval_runtime_parity.py`; `python scripts/eval_recall.py --top-k 4` |
| **Safety** | Deny/fallback constraints are enforced (uncited factual responses rejected, progressive fallback policy constraints are preserved (clarify/assist/explicit uncertainty), and fallback policy actions remain deterministic under ambiguity/capability states). | `features/testbot/answer_contract.feature`, `features/testbot/memory_recall.feature`, `src/testbot/reflection_policy.py`, `tests/test_reflection_policy.py`, `tests/test_runtime_logging_events.py`, `scripts/validate_log_schema.py`. | `python -m behave features/testbot/answer_contract.feature features/testbot/memory_recall.feature`; `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py`; `python scripts/validate_log_schema.py` |
| **Ops** | Startup capability degradations are explicit and deterministic (auto-mode fallback to CLI when HA is unavailable, startup status reports degraded vs active capability). | `src/testbot/sat_chatbot_memory_v2.py` (`_resolve_mode`, `_print_startup_status`), `tests/test_runtime_modes.py`, `tests/test_startup_status.py`. | `python -m pytest tests/test_runtime_modes.py tests/test_startup_status.py` |
| **QA** | Deterministic test gates and fixtures stay stable, synchronized, and traceable to canonical eval data. | `tests/test_eval_fixtures.py`, `tests/test_eval_runtime_parity.py`, `tests/fixtures/candidate_sets.jsonl`, `eval/cases.jsonl`, `scripts/validate_issue_links.py`, `scripts/validate_invariant_sync.py`, `scripts/validate_markdown_paths.py`. | `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_fixtures.py tests/test_eval_runtime_parity.py`; `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`; `python scripts/validate_invariant_sync.py`; `python scripts/validate_markdown_paths.py` |

### Roadmap snapshot consistency hygiene

To keep roadmap readiness narratives aligned with generated evidence, run the roadmap consistency validator after refreshing gate/report artifacts:

```bash
python scripts/validate_roadmap_consistency.py
```

This check warns/fails when any of the following drift conditions appear:

- `docs/roadmap/current-status-and-next-5-priorities.md` snapshot timestamp is older than the configured freshness threshold versus `artifacts/all-green-gate-summary.json` artifact mtime.
- Roadmap gate status field does not match the gate summary JSON top-level `status`.
- Roadmap capability summary line does not match the summary block in `docs/qa/feature-status-report.md`.

Use `--max-staleness-seconds <N>` to tune freshness policy (default `86400`). For stale output, follow the script's exact refresh commands and then update the roadmap snapshot fields in-place.

### Uncovered obligations and added checks

The Ops obligation previously lacked a deterministic assertion that degraded startup messaging explicitly documents CLI fallback behavior and continuity messaging. This is now covered by `test_startup_status_prints_degraded_cli_fallback_note_and_continuity_message` in `tests/test_startup_status.py`.

### Explicit "all systems green" criteria

"All systems green" requires a successful canonical gate run (`python scripts/all_green_gate.py`) and all criteria below in the same change window:

1. **Stage contract suite pass**: stage contract coverage for canonical turn stages passes (via deterministic pytest coverage and canonical conformance validators).
2. **Decision matrix pass**: matrix-style policy/branching checks pass for intent/evidence/capability combinations.
3. **Provenance/grounding suite pass**: provenance binding, citation completeness, and grounding safety checks pass (BDD + deterministic targeted suites).
4. **KPI thresholds pass**: fallback and invalid-answer quality guardrails meet configured thresholds in `config/kpi_guardrails.json`:
   - `fallback_appropriateness >= 0.70`
   - `false_knowing_rate <= 0.05`

Failure conditions (must block readiness):

- `python scripts/all_green_gate.py` exits non-zero for any blocking check category.
- Any required suite above has failing tests/validators.
- KPI guardrails violate thresholds in blocking mode, or remain unresolved warning debt contrary to repository governance policy in optional mode.

If any failure condition is present, the repository is not considered green for merge readiness.

## Rerank objective under test (canonical)

Named objective: `semantic_temporal_type_v1`.

Formula:

```text
final_score = semantic_score * type_prior * (base_temporal_blend + gaussian_temporal_blend * temporal_gaussian_weight)
```

Canonical parameters:

| Parameter | Default | Rationale |
| --- | --- | --- |
| `base_temporal_blend` | `0.25` | Preserves baseline semantic influence even when temporal evidence is weak/noisy. |
| `gaussian_temporal_blend` | `0.75` | Gives temporal alignment dominant but bounded influence when timestamp proximity is strong. |
| `reflection_type_prior` | `0.7` | Slightly down-weights reflection cards versus direct utterance/memory cards to reduce speculative wins. |
| `default_type_prior` | `1.0` | Keeps non-reflection card types unpenalized by default. |

When tuning, change coefficients as controlled parameter updates and validate with `python scripts/eval_recall.py` attribution output (`objective_component_attribution`) rather than branch-local scoring rewrites.

## Deterministic fixture catalog

Fixture files live in `eval/` (source eval patterns) and `tests/fixtures/` (test-owned snapshots):

- `eval/cases.jsonl`: canonical scenario patterns (`case_id`, utterance, expected intent/doc, candidate sets).
- `tests/fixtures/fixed_timestamps.json`: fixed reference clock for deterministic temporal checks.
- `tests/fixtures/candidate_sets.jsonl`: selected candidate-set snapshots linked back to `source_case_id` in `eval/cases.jsonl`.

### Naming convention

- Use `kebab-case` ids with semantic prefixes:
  - Eval cases: `case_id` such as `sleep-followup`, `no-memory-match`.
  - Fixture snapshots: `fixture_id` such as `candidate-set-sleep-followup`.
- Include `source_case_id` in fixture snapshots whenever data originates from `eval/cases.jsonl`.

### Update policy (who / when / why)

- **Who**: the code owner of retrieval/rerank behavior (or designated QA maintainer) updates fixtures in the same PR as behavior changes.
- **When**: update fixtures when expected retrieval intent/doc changes, candidate composition changes materially, or a new stakeholder-visible memory scenario is added.
- **Why**: keep BDD and unit checks deterministic, traceable to the same canonical patterns, and resistant to drift/flakiness.

## Acceptance criteria checklist

- [ ] Stakeholder-visible behavior is covered by BDD scenarios.
- [ ] Default test suite remains deterministic and offline.
- [ ] Citation/fallback answer contract is explicitly tested.
- [ ] Temporal rerank behavior is validated with fixed-time fixtures.

## Governance cadence for drift control

Use this recurring cadence to keep behavior, policy artifacts, and issue records aligned:

- **Sprint cadence (mini drift review at sprint close):**
  - Review behavior changes merged during the sprint for traceability gaps.
  - Confirm any touched directives/invariants and issue records remain aligned with shipped behavior.
- **Release cadence (full drift review before release cut):**
  - Run a full drift review across behavior specs, runtime docs, invariants/directives, and issue governance artifacts.
  - Treat unresolved drift as a release blocker until reconciled.

### Drift review ownership roles

Assign explicit reviewers for each governance area:

- **Architecture reviewer:** validates architectural consistency and confirms touched behavior still matches documented runtime design boundaries.
- **Behavior contract reviewer:** validates BDD and deterministic tests reflect stakeholder-visible behavior and fallback/citation contract requirements.
- **Issue hygiene reviewer:** validates issue status transitions, acceptance criteria reconciliation, and issue-link integrity.

## PR and release governance checklist

For every PR and release candidate, complete this checklist in addition to feature/testing checks:

- [ ] **Traceability matrix updates:** matrix rows are updated for every changed stakeholder-visible behavior.
- [ ] **Issue criterion reconciliation:** when issue status changes, issue criteria and status rationale are reconciled in the corresponding issue artifact.
- [ ] **Directive/invariant cross-check:** all touched behavior is cross-checked against applicable directives and invariants, with docs/code aligned.
- [ ] **Canonical validation gate run:** `python scripts/all_green_gate.py` executed and passing.
- [ ] **Issue validators run when issue artifacts are touched:**
  - `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
  - `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
