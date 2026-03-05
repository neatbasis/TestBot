# TestBot

## What
TestBot is a memory-grounded chatbot loop for Home Assistant Assist Satellite.

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


### Current vs Planned
The tree below distinguishes files that exist today from placeholders planned for future work.

#### Current repository tree
```text
.
├── CONTRIBUTING.md
├── README.md
├── docs/
│   ├── architecture.md
│   ├── directives/
│   │   ├── CHANGE_POLICY.md
│   │   ├── invariants.md
│   │   ├── source-map.md
│   │   ├── terms.md
│   │   └── traceability-matrix.md
│   ├── ops.md
│   ├── quickstart.md
│   ├── style-guide.md
│   └── testing.md
├── eval/
│   └── cases.jsonl
├── features/
│   ├── README.md
│   ├── answer_contract.feature
│   ├── memory_recall.feature
│   └── steps/
│       ├── answer_contract_steps.py
│       └── memory_steps.py
├── pyproject.toml
├── scripts/
│   ├── eval_recall.py
│   ├── release_gate.py
│   ├── validate_issue_links.py
│   └── validate_markdown_paths.py
└── src/
    └── testbot/
        ├── __init__.py
        ├── config.py
        ├── memory_cards.py
        ├── rerank.py
        ├── sat_chatbot_memory_v2.py
        └── time_parse.py
```

#### Planned (not in repo yet)
- `prompts.py`
- `scripts/run_sat.sh`

## Setup
From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Development extras (required to run `behave` and other dev checks):

```bash
pip install -e .[dev]
```

`behave` is installed via the `dev` extra, so install this before running behavior scenarios.

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

Run this governance gate locally before requesting review or merge:

```bash
python scripts/release_gate.py
```

## Validate
- Canonical merge/release gate: `python scripts/release_gate.py`
- Optional run-all mode (collect every failure before exiting non-zero): `python scripts/release_gate.py --continue-on-failure`
- Machine-readable summary artifact: `python scripts/release_gate.py --json-output artifacts/release-gate-summary.json`
- Run optional live smoke profile: `pytest -m live_smoke`
- Optional docs path validation: `python scripts/validate_markdown_paths.py`

### Quick contributor validation

For non-live code changes, use this offline/deterministic gate:

1. `pip install -e .[dev]`
2. `python scripts/release_gate.py`

See [docs/testing.md](docs/testing.md) for test-layer policy and acceptance criteria.

The canonical definition of **"all systems green"** is the stakeholder obligations matrix in [docs/directives/stakeholder-obligations.md](docs/directives/stakeholder-obligations.md).

## Contribute
Please follow [CONTRIBUTING.md](CONTRIBUTING.md) and use [docs/style-guide.md](docs/style-guide.md) for documentation style.
