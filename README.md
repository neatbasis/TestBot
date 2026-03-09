# TestBot

## What
TestBot is a stateful, retrieval-augmented conversational agent with persistent memory and multi-interface interaction.

### Terminology (ontology crosswalk)
- **turn pipeline** → agent inference pipeline
- **memory cards** → episodic memory store
- **vector store retrieval** → retrieval-augmented generation (RAG)
- **durable facts** → persistent memory / long-term memory
- **CLI / satellite** → interaction interfaces
- **structured logs** → telemetry / observability
- **context resolution** → context management
- **commit stage** → memory update / memory consolidation

Internal names remain canonical identifiers; standard terms are provided for wider community readability.

### Cognitive architecture alignment
TestBot's pipeline mirrors a perception → memory → reasoning → action model:

| Cognitive architecture | TestBot concept |
| --- | --- |
| perception | observe stage |
| encoding | encode stage |
| working memory | canonical state |
| episodic memory | vector store |
| reasoning | inference |
| action | answer generation |
| learning | commit stage |

## Vision
TestBot is a user-steered assistant that combines conversational memory with ingested external sources to produce evidence-backed responses without overstating certainty or autonomy.

For stakeholder-critical outputs, trust must be measurable: responses should be attributable to explicit evidence references (for example `used_source_evidence_refs` plus `source_evidence_attribution` / `used_memory_refs` metadata) and fallback decisions should remain policy-explainable through directive traceability artifacts such as [docs/directives/traceability-matrix.md](docs/directives/traceability-matrix.md) and [docs/directives/source-map.md](docs/directives/source-map.md).

Non-goal: TestBot does not claim perfect truth, complete source coverage, or universally correct answers across all domains.

### How Vision is operationalized

Policy-facing, testable product principles that operationalize Vision claims are defined in [docs/directives/product-principles.md](docs/directives/product-principles.md).
- **Evidence-backed knowing responses**: source ingestion continuously normalizes external evidence into retrievable records, and knowing-mode answers include provenance so users can inspect what memory and source evidence informed the response.
- **Explicit uncertainty when evidence is weak or conflicting**: trust-tier metadata is preserved for ingested sources, and disagreement between memory and source evidence resolves to visible uncertainty/clarification behavior rather than unsupported claims.
- **Safe fallback and clarifier behavior**: deterministic fallback policy routes low-trust, unavailable, or conflicting evidence to safe fallback paths, including user-facing clarification prompts.

### Continuity commitments
- **`answer.commit` is mandatory continuity write-through**: each turn must persist confirmed user facts, obligations, repair state, and assistant-turn provenance so follow-up turns inherit durable state instead of re-deriving it.
- **Continuity evidence must stay traceable**: retrieval/context layers must treat `commit_receipt` artifacts (memory update receipts) as first-class continuity evidence so downstream behavior can point to committed anchors, not implicit guesswork.
- **Persistence must preserve user agency over time**: carrying forward explicit commitments lets users correct facts, close obligations, and steer repairs across turns with auditable state transitions.

TestBot operates in two explicit response intents:

- **Knowing mode**: provide an evidence-backed grounded answer with provenance for where the answer came from.
- **Unknowing mode**: do not fabricate; explicitly state uncertainty, keep confidence calibration visible to the user, and either ask for clarification or provide a safe fallback path.

### Start here by role
- **Operator**: read [docs/quickstart.md](docs/quickstart.md).
- **Developer / QA**: read [docs/testing.md](docs/testing.md).
- **Designer / reviewer**: read [docs/architecture.md](docs/architecture.md).

## Issue tracking (canonical, in-repo)

Project issue tracking is now standardized in-repo and remains the default workflow **until reviewed**.

- Canonical workflow: `docs/issues.md`
- Issue records: `docs/issues/`
- Red-tag escalation index: `docs/issues/RED_TAG.md`
- Current canonical pipeline program: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; align canonical turn pipeline (agent inference pipeline) delivery planning from `ISSUE-0012` under this program first.

Use issue IDs (for example `ISSUE-0002`) in PR descriptions and non-trivial commit messages for any non-trivial change.

---
### Repository map (maintained)
Use this high-level map instead of a full tree snapshot:

- `src/testbot/` — runtime chatbot loop, memory recall, ranking, and mode orchestration.
- `features/` — behavior scenarios for answer contract, memory recall, and intent grounding.
- `tests/` — unit/integration-style Python test coverage.
- `docs/` — architecture, directives, testing policy, operations notes, and roadmap/status docs.
- `scripts/` — release gates and validation/automation helpers.
- `eval/` — evaluation fixtures and supporting artifacts.

For canonical project status and planned work, use `docs/roadmap/`.

## Grounding model
Authoritative grounding/intent references:

- [docs/architecture.md](docs/architecture.md)
- [features/intent_grounding.feature](features/intent_grounding.feature)
- [docs/directives/traceability-matrix.md](docs/directives/traceability-matrix.md)

## Current limitations
- External fact integrations are currently limited.
- Most grounding comes from conversation memory plus deterministic policy/routing behavior.
- For current validation expectations, see [docs/testing.md](docs/testing.md).
- For roadmap and delivery status, see [docs/roadmap/](docs/roadmap/).

## Setup by persona
From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
```

### Operator / runtime only

Install only runtime dependencies:

```bash
pip install -e .
```

### Contributor / QA (validation enabled)

Install the canonical contributor environment:

```bash
pip install -e .[dev]
```

`.[dev]` includes runtime dependencies plus validation tooling (for example `pytest` and `behave`). If `behave` is missing, your setup is incomplete—see the canonical note in [docs/testing.md](docs/testing.md#bdd-tooling-health-check-canonical).

For full environment prerequisites and `.env` variables, use [docs/quickstart.md](docs/quickstart.md).

## Run
Start in auto mode (prefers Home Assistant satellite, falls back to CLI chat):

```bash
testbot --mode auto
```

Other common modes:

```bash
testbot --mode satellite
testbot --mode cli
testbot --mode satellite --daemon
```

Alternative direct module run:

```bash
python src/testbot/sat_chatbot_memory_v2.py
```


## Required before merge

Run the single authoritative all-systems-green gate locally before requesting review or merge:

```bash
python scripts/all_green_gate.py
```

## Validate
- **Only authoritative merge/readiness sequence**: `python scripts/all_green_gate.py`
- BDD execution inside the canonical gate is a hard prerequisite for interpreting feature-status evidence as behavior confidence. If preflight reports missing `behave`, remediate with `python -m pip install -e .[dev]` before trusting capability status.
- Optional run-all mode (same sequence, continues after failures): `python scripts/all_green_gate.py --continue-on-failure`
- Machine-readable summary artifact for the same sequence: `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json`
- Optional post-merge live smoke profile: `pytest -m live_smoke`

### Turn analytics in canonical gate

`scripts/all_green_gate.py` now mirrors release-gate rollout behavior for turn analytics KPI checks via `--kpi-guardrail-mode {off,optional,blocking}` (default `optional`).

- `off`: skips turn analytics aggregation and KPI guardrail validation.
- `optional`: runs `scripts/aggregate_turn_analytics.py` and `scripts/validate_kpi_guardrails.py` as non-blocking warnings.
- `blocking`: runs the same commands as hard failures that block gate success.

### Quick contributor validation

For non-live code changes, use this offline/deterministic gate:

1. `pip install -e .[dev]`
2. `python scripts/all_green_gate.py`

See [docs/testing.md](docs/testing.md) for test-layer policy and acceptance criteria.

The canonical definition of **"all systems green"** is the stakeholder obligations matrix in [docs/directives/stakeholder-obligations.md](docs/directives/stakeholder-obligations.md).

## Contribute
Please follow [CONTRIBUTING.md](CONTRIBUTING.md) and use [docs/style-guide.md](docs/style-guide.md) for documentation style.
