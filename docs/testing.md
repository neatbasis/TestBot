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

## Test layers

### 1) BDD scenarios (`behave`)

Use BDD to validate externally visible outcomes:

- Memory-grounded responses include `doc_id` and `ts` when context is sufficient.
- Assistant returns exact fallback `I don't know from memory.` when context is insufficient.
- Time-aware retrieval behavior matches expected outcomes for representative phrasing.

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
- Assert stable top-k ordering and fallback behavior

### 4) Optional live integration smoke tests

Run separately against real Home Assistant + Ollama for environment confidence. Keep these tests opt-in and out of default quick runs.

## Commands

Use the following canonical commands from repository root.

### Quick contributor validation

For non-live changes, this is the expected offline/deterministic contributor sequence in exact order:

1. `pip install -e .[dev]`
2. `behave`
3. `pytest -m "not live_smoke"`
4. `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`

| Test layer | Canonical command | Runtime dependency | CI gate level | Expected runtime | Pass criteria |
| --- | --- | --- | --- | --- | --- |
| BDD acceptance (`behave`) | `behave` _(requires `pip install -e .[dev]` first)_ | Python dev extras (`behave`) and local deterministic fixtures | **Required (merge gate)** | ~10-60s for current feature set | Exit code `0`; no failed/undefined steps; acceptance scenarios for changed behavior pass. |
| Deterministic unit/component (`pytest`) | `pytest -m "not live_smoke"` | Python dev extras (`pytest`); no network or external services | **Required (merge gate)** | ~5-30s for fast deterministic scope | Exit code `0`; no flaky network-bound failures; logic and wiring tests for changed code pass. |
| Eval/runtime parity check (`pytest`) | `pytest tests/test_eval_runtime_parity.py` | Python dev extras (`pytest`) and fixed fixtures (`eval/cases.jsonl`, `tests/fixtures/candidate_sets.jsonl`) | **Required (merge gate, deterministic)** | ~1-5s | Exit code `0`; runtime path scoring and eval adapter path stay aligned for ordering, top-1, and fallback intent decisions. |
| Governance / issue linkage checks | `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` | Local git metadata + docs/issues files | **Required (merge gate)** | ~1-5s | Exit code `0`; non-trivial PR/commit metadata include `ISSUE-XXXX`; red-severity ownership/sprint/status and canonical issue schema checks pass. |
| Optional live smoke profile | `pytest -m live_smoke` | Reachable Home Assistant + Ollama endpoints and any required env vars/secrets | **Optional (post-merge/manual gate)** | ~1-5 min depending on services | Exit code `0`; no infra/auth/connectivity errors; end-to-end smoke assertions pass. |

### Canonical command snippets

Run BDD scenarios (requires `pip install -e .[dev]` first):

```bash
behave
```

Run deterministic unit/component tests only:

```bash
pytest -m "not live_smoke"
```

Run deterministic eval/runtime parity gate:

```bash
pytest tests/test_eval_runtime_parity.py
```

Run optional live smoke profile:

```bash
pytest -m live_smoke
```

Run governance and issue-linkage checks:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
```


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
