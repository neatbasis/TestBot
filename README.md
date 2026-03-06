# TestBot

## What
TestBot is a memory-grounded chatbot loop for Home Assistant Assist Satellite.

TestBot operates in two explicit response intents:

- **Knowing mode**: provide a grounded answer based on available evidence and include provenance for where the answer came from.
- **Unknowing mode**: do not fabricate; explicitly state uncertainty and either ask for clarification or provide a safe fallback path.

### Start here by role
- **Operator**: read [docs/quickstart.md](docs/quickstart.md).
- **Developer / QA**: read [docs/testing.md](docs/testing.md).
- **Designer / reviewer**: read [docs/architecture.md](docs/architecture.md).

## Issue tracking (canonical, in-repo)

Project issue tracking is now standardized in-repo and remains the default workflow **until reviewed**.

- Canonical workflow: `docs/issues.md`
- Issue records: `docs/issues/`
- Red-tag escalation index: `docs/issues/RED_TAG.md`

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

## Setup
From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pip install -e .[dev]
```

`behave` is installed via the `dev` extra, so install this before running behavior scenarios.
Treat missing `behave` as a setup failure (not an acceptable skip): canonical validation is fail-closed on BDD.

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
- Optional run-all mode (same sequence, continues after failures): `python scripts/all_green_gate.py --continue-on-failure`
- Machine-readable summary artifact for the same sequence: `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json`
- Optional post-merge live smoke profile: `pytest -m live_smoke`

### Quick contributor validation

For non-live code changes, use this offline/deterministic gate:

1. `pip install -e .`
2. `pip install -e .[dev]`
3. `python scripts/all_green_gate.py`

See [docs/testing.md](docs/testing.md) for test-layer policy and acceptance criteria.

The canonical definition of **"all systems green"** is the stakeholder obligations matrix in [docs/directives/stakeholder-obligations.md](docs/directives/stakeholder-obligations.md).

## Contribute
Please follow [CONTRIBUTING.md](CONTRIBUTING.md) and use [docs/style-guide.md](docs/style-guide.md) for documentation style.
