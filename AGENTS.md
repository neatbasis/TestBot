# AGENTS.md

## Purpose
This file is the canonical bootstrap contract for AI coding agents working in TestBot.

Use it to determine:
- how to install and run validation,
- which project artifacts are authoritative,
- what constraints must hold before a change is considered complete.

## Repository orientation
- Runtime code: `src/testbot/`
- Behavior specs: `features/`
- Unit/component tests: `tests/`
- Operational and governance docs: `docs/`
- Validation and release helpers: `scripts/`
- Evaluation fixtures: `eval/`

Start with:
1. `README.md`
2. `docs/architecture.md`
3. `docs/testing.md`
4. `docs/directives/stakeholder-obligations.md`

## Environment setup
From repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

`behave` is required for canonical validation and is provided by the `dev` extra.

## Canonical validation contract
Before considering a task complete, run the authoritative merge/readiness gate:

```bash
python scripts/all_green_gate.py
```

Optional variants:

```bash
python scripts/all_green_gate.py --continue-on-failure
python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json
```

If targeted checks are needed during iteration, use:

```bash
python -m behave
python -m pytest -m "not live_smoke"
python -m pytest tests/test_eval_runtime_parity.py
```

## Behavior contract
TestBot has two explicit response intents:
- **Knowing mode**: grounded response with provenance.
- **Unknowing mode**: no fabrication; explicit uncertainty and safe fallback/clarifier behavior.

For any stakeholder-visible behavior change, update/add BDD scenarios first (`features/*.feature`) and keep deterministic tests aligned.

## Governance and issue workflow
Use in-repo issue workflow:
- Canonical process: `docs/issues.md`
- Issue records: `docs/issues/`
- Red-tag escalation index: `docs/issues/RED_TAG.md`

Non-trivial changes should include an issue ID like `ISSUE-0001` in commit/PR metadata.

Run issue and policy validators when modifying issue artifacts or release metadata:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
```

## Invariants and directives
Treat the following as authoritative constraints:
- `docs/invariants.md`
- `docs/directives/`

When code behavior and documentation disagree, update both in the same change set so repository policy and implementation remain in sync.

## Safety and change discipline
- Prefer deterministic/offline tests by default.
- Keep live smoke checks opt-in (`-m live_smoke`).
- Do not weaken validation gates to make a failing change appear green.
- Keep edits minimal, traceable, and scoped to the requested task.

## Definition of done for agents
A change is done when all are true:
1. Requested behavior/docs are implemented.
2. Canonical validation gate passes locally.
3. Related docs/tests are updated.
4. No contradictions remain between runtime behavior, tests, and directives.
