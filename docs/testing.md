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

Run BDD scenarios:

```bash
behave
```

Run unit/component tests (when present):

```bash
pytest
```

## Acceptance criteria checklist

- [ ] Stakeholder-visible behavior is covered by BDD scenarios.
- [ ] Default test suite remains deterministic and offline.
- [ ] Citation/fallback answer contract is explicitly tested.
- [ ] Temporal rerank behavior is validated with fixed-time fixtures.
