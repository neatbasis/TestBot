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

## BDD-first policy

Behavior that stakeholders care about must be written first as `.feature` scenarios. Implementation is complete only when those scenarios pass and deterministic supporting tests confirm lower-level logic.

## Scenario traceability quick map

For fast failure triage across behavior specs, runtime anchors, and deterministic tests, use [docs/feature-runtime-test-traceability.md](feature-runtime-test-traceability.md).

## Test layers

### 1) BDD scenarios (`behave`)

Use BDD to validate externally visible outcomes:

- Memory-grounded responses include `doc_id` and `ts` when context is sufficient.
- Assistant uses progressive fallback when memory is insufficient: ask one targeted clarifier or offer at least two capability-based alternatives; reserve exact `I don't know from memory.` for explicit deny/safety-only cases.
- Time-aware retrieval behavior matches expected outcomes for representative phrasing.

`behave` is mandatory for canonical merge validation. If `behave` is missing, treat that as a local setup defect and
fix it with `pip install -e .[dev]` before considering validation complete.

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

## Commands

Use the following canonical commands from repository root.

### Quick contributor validation

For non-live changes, this is the expected offline/deterministic contributor gate:

1. `pip install -e .`
2. `pip install -e .[dev]`
3. `python scripts/all_green_gate.py`

`scripts/all_green_gate.py` is the only authoritative command sequence for merge readiness. By default it runs a **fast** profile that preserves category coverage while avoiding redundant targeted checks already covered by broader suites (for example, `pytest -m "not live_smoke"` and full `behave`).

Use `--check-profile exhaustive` to include overlapping targeted checks (for example, focused parity and subset-behave invocations) when you need deeper diagnostics.

Default behavior is fail-closed (stop on first failure). Use `--continue-on-failure` to run every check and still exit non-zero if any check fails.

### Turn analytics in canonical gate

The canonical gate (`scripts/all_green_gate.py`) supports KPI rollout controls via `--kpi-guardrail-mode {off,optional,blocking}` (default: `optional`). In `optional`, `scripts/aggregate_turn_analytics.py` and `scripts/validate_kpi_guardrails.py` run as non-blocking warnings; in `blocking`, the same failures block gate success; in `off`, both checks are skipped.

| Test layer | Canonical command | Runtime dependency | CI gate level | Expected runtime | Pass criteria |
| --- | --- | --- | --- | --- | --- |
| Single merge/readiness gate (fast profile) | `python scripts/all_green_gate.py` | Python dev extras (`behave`, `pytest`) plus local docs/issues/fixtures and git metadata | **Required (canonical gate)** | ~30-150s depending on test volume | Exit code `0`; category-level blocking checks pass (BDD, deterministic pytest, recall eval, governance + invariant/path/schema validators) without redundant targeted overlap commands. |
| BDD acceptance (`behave`) | `python -m behave` _(requires `pip install -e .[dev]` first)_ | Python dev extras (`behave`) and local deterministic fixtures | **Executed by canonical gate (component check)** | ~10-60s for current feature set | Exit code `0`; no failed/undefined steps; acceptance scenarios for changed behavior pass. |
| Deterministic unit/component (`pytest`) | `python -m pytest -m "not live_smoke"` | Python dev extras (`pytest`); no network or external services | **Executed by canonical gate (component check)** | ~5-30s for fast deterministic scope | Exit code `0`; no flaky network-bound failures; logic and wiring tests for changed code pass. |
| Eval/runtime parity check (`pytest`) | `python -m pytest tests/test_eval_runtime_parity.py` | Python dev extras (`pytest`) and fixed fixtures (`eval/cases.jsonl`, `tests/fixtures/candidate_sets.jsonl`) | **Executed by canonical gate in `--check-profile exhaustive`** | ~1-5s | Exit code `0`; runtime path scoring and eval adapter path stay aligned for ordering, top-1, and fallback intent decisions. |
| Governance / issue linkage checks | `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` | Local git metadata + docs/issues files | **Executed by canonical gate (component check)** | ~1-5s | Exit code `0`; non-trivial PR/commit metadata include `ISSUE-XXXX`; canonical fields are non-placeholder; required issue section bodies are non-empty; red-severity ownership/sprint/status and RED_TAG consistency checks pass. |
| Policy compatibility checks | `python scripts/validate_issues.py --all-issue-files --base-ref origin/main` | Local git metadata + docs/issues files | **Executed by canonical gate (component check)** | ~1-5s | Exit code `0`; compatibility validator reports no missing canonical sections and no red-tag owner/sprint gaps. |
| Optional live smoke profile | `pytest -m live_smoke` | Reachable Home Assistant + Ollama endpoints and any required env vars/secrets | **Optional (post-merge/manual gate)** | ~1-5 min depending on services | Exit code `0`; no infra/auth/connectivity errors; end-to-end smoke assertions pass. |

### Dependency policy for test tooling

- `behave` and `pytest` are **development/test dependencies**, not runtime dependencies of the `testbot` application process.
- Keep them in the `dev` extra (`pip install -e .[dev]`) so production installs stay minimal while merge gates remain enforceable.
- Canonical gate commands should invoke test tools through the active interpreter (`python -m behave`, `python -m pytest`) to reduce PATH-related false failures.

### Canonical command snippets

Run canonical merge/release gate:

```bash
python scripts/all_green_gate.py
```

Run gate in run-all mode (returns non-zero if any check failed):

```bash
python scripts/all_green_gate.py --continue-on-failure
```

Run canonical gate with exhaustive overlap checks:

```bash
python scripts/all_green_gate.py --check-profile exhaustive
```

Write gate results to a JSON artifact (for CI/log processing):

```bash
python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json
```

Run BDD scenarios directly (requires `pip install -e .[dev]` first):

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
TESTBOT_ENABLE_LIVE_SMOKE=1 \
python -m pytest tests/test_live_smoke_ollama.py -m live_smoke -vv
```

Expected outcomes for `tests/test_live_smoke_ollama.py`:

- If `TESTBOT_ENABLE_LIVE_SMOKE` is not set to `1` (or `true`/`yes`), the module is skipped so live tests do not run accidentally.
- If prerequisites are set and Ollama is reachable with both models pulled, both tests pass.
- If `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, or `OLLAMA_EMBEDDING_MODEL` are missing, tests skip with explicit guidance naming the missing variable.
- If endpoint/model provisioning is incorrect, tests fail with a live connectivity/model error (intentional signal that environment is not ready).


Run degraded-mode live smoke scenarios only (`tests/test_live_smoke_degraded_modes.py`):

```bash
# Scenario matrix exercised by this module:
# 1) HA unavailable + Ollama available
# 2) HA available + Ollama unavailable
# 3) both unavailable
#
# Required baseline live env vars:
# - TESTBOT_ENABLE_LIVE_SMOKE=1
# - OLLAMA_BASE_URL / OLLAMA_MODEL / OLLAMA_EMBEDDING_MODEL (for the "Ollama available" scenario)
# - HA_API_URL / HA_API_SECRET / HA_SATELLITE_ENTITY_ID (for the "HA available" scenario)
#
# Failure injection for degraded scenarios is environment-driven only. The test module
# swaps endpoints to unreachable localhost ports (HA: 127.0.0.1:9, Ollama: 127.0.0.1:1)
# and does not monkeypatch runtime connectivity helpers.
TESTBOT_ENABLE_LIVE_SMOKE=1 \
OLLAMA_BASE_URL=http://localhost:11434 \
OLLAMA_MODEL=llama3.1:latest \
OLLAMA_EMBEDDING_MODEL=nomic-embed-text \
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
- If `origin/main` is unavailable (for example, shallow/detached clones), fall back in order to `HEAD~1`, then `HEAD`.
- This fallback behavior is by design (contracted), and the gate emits a warning note when fallback is used.
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

### Step 2: Run the canonical full gate

```bash
python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json
```

### Step 3: Run stakeholder-obligation checks explicitly

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
```

If `origin/main` is not present locally (common in shallow CI clones), follow the canonical policy (automatic fallback to `HEAD~1`, then `HEAD`) or fetch explicitly:

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
3. Governance validators exit `0` under canonical base-ref policy (`origin/main` default; fallback `HEAD~1` then `HEAD` when unavailable).
4. PR body contains evidence artifact paths and references the run generated after conflict resolution.


## All-systems-green definition

The canonical merge-readiness definition of **"all systems green"** is the stakeholder obligations matrix in [docs/directives/stakeholder-obligations.md](directives/stakeholder-obligations.md).

Use the matrix as the authoritative map from stakeholder obligations to required deterministic evidence.

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
