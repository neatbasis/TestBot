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
4. `docs/testing.md#readiness-evidence-all-systems-green-criteria`

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

## MCP Operating Guidance (Infrastructure Scope)
TestBot uses a project-scoped MCP stack. Use these tools to keep agent work evidence-backed and bounded.

### GitNexus (repo archaeology, impact, bounded cuts)
- Use `query` and `context` first when code ownership or execution flow is unclear.
- Use graph evidence to trace decision/routing authority before changing stage boundaries or policy wiring.
- Run `impact` before editing runtime symbols and use blast radius to choose the smallest safe cut.
- Run `detect_changes` before commit to confirm changed symbols/processes match the intended scope.
- Prefer graph-backed traces over grep-only archaeology for non-trivial behavior changes.

### Context7 (version-sensitive external API truth)
- For external libraries, frameworks, SDKs, and cloud APIs, resolve the library ID and query current docs before changing behavior.
- Use Context7 output to confirm API signatures, configuration flags, migration notes, and default behavior.
- Do not rely on memory for version-sensitive APIs.

### Supabase MCP (schema/state inspection before DB proposals)
- Current configuration is read-only and feature-scoped (`database,docs,debugging`).
- Use Supabase MCP to inspect schemas, tables, extensions, advisors, and logs before proposing DB changes.
- Treat Supabase output as environment evidence; document missing schema/state rather than assuming it exists.
- Read-only mode intentionally disables mutating workflows; this process PR does not activate broad DDL/data mutation rollout.

### Sentry MCP (evidence-backed debugging once events exist)
- Use Sentry MCP to list issues, inspect event context, and prioritize fixes by observed impact.
- If Sentry returns no issues/events, state that runtime evidence is not yet available.
- Do not infer production failure patterns without Sentry data.
- Sentry MCP does not replace SDK instrumentation or release metadata wiring.
- Connectivity alone is not observability value; actionable triage requires emitted runtime events and release context.

### Non-Goals For Infrastructure/Process PRs
- Do not combine MCP process updates with broad application schema rollout.
- Do not combine MCP process updates with broad observability instrumentation rollout.
- Keep these PRs focused on configuration, guidance, and safe workflow guardrails.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **TestBot** (7225 symbols, 15674 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/TestBot/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/TestBot/context` | Codebase overview, check index freshness |
| `gitnexus://repo/TestBot/clusters` | All functional areas |
| `gitnexus://repo/TestBot/processes` | All execution flows |
| `gitnexus://repo/TestBot/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
