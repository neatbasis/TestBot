# Stakeholder obligations matrix

This document defines the minimum evidence for saying **"all systems green"** in this repository.

An obligation is green only when:

1. a stakeholder-facing requirement is mapped to concrete artifacts,
2. deterministic checks for that requirement pass, and
3. required merge gates in [docs/testing.md](../testing.md) pass.

## Obligation-to-artifact mapping

| Stakeholder domain | Obligation | Concrete artifacts | Deterministic checks (must pass) |
| --- | --- | --- | --- |
| **Product** | Utility behavior scenarios remain user-trustworthy (memory-grounded answers when evidence exists, progressive clarify/assist fallback when it does not, intent-grounded non-memory responses with explicit basis). | `features/memory_recall.feature`, `features/answer_contract.feature`, `features/intent_grounding.feature`, step harnesses under `features/steps/`. | `behave`; `pytest tests/test_eval_runtime_parity.py`; `python scripts/eval_recall.py --top-k 4` |
| **Safety** | Deny/fallback constraints are enforced (uncited factual responses rejected, progressive fallback policy constraints are preserved (clarify/assist/explicit uncertainty), and fallback policy actions remain deterministic under ambiguity/capability states). | `features/answer_contract.feature`, `features/memory_recall.feature`, `src/testbot/reflection_policy.py`, `tests/test_reflection_policy.py`, `tests/test_runtime_logging_events.py`, `scripts/validate_log_schema.py`. | `behave features/answer_contract.feature features/memory_recall.feature`; `pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py`; `python scripts/validate_log_schema.py` |
| **Ops** | Startup capability degradations are explicit and deterministic (auto-mode fallback to CLI when HA is unavailable, startup status reports degraded vs active capability). | `src/testbot/sat_chatbot_memory_v2.py` (`_resolve_mode`, `_print_startup_status`), `tests/test_runtime_modes.py`, `tests/test_startup_status.py`. | `pytest tests/test_runtime_modes.py tests/test_startup_status.py` |
| **QA** | Deterministic test gates and fixtures stay stable, synchronized, and traceable to canonical eval data. | `tests/test_eval_fixtures.py`, `tests/test_eval_runtime_parity.py`, `tests/fixtures/candidate_sets.jsonl`, `eval/cases.jsonl`, `scripts/validate_issue_links.py`, `scripts/validate_invariant_sync.py`, `scripts/validate_markdown_paths.py`. | `pytest -m "not live_smoke"`; `pytest tests/test_eval_fixtures.py tests/test_eval_runtime_parity.py`; `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`; `python scripts/validate_invariant_sync.py`; `python scripts/validate_markdown_paths.py` |

## Uncovered obligations and added checks

The Ops obligation previously lacked a deterministic assertion that degraded startup messaging explicitly documents CLI fallback behavior and continuity messaging. This is now covered by `test_startup_status_prints_degraded_cli_fallback_note_and_continuity_message` in `tests/test_startup_status.py`.

## "All systems green" definition

"All systems green" means every obligation row above has passing deterministic evidence in the same change window:

1. Product behavior scenarios pass (`behave`).
2. Safety deny/fallback checks pass (`behave` + targeted `pytest` + schema validation).
3. Ops startup degradation checks pass (runtime mode + startup status tests).
4. QA fixture/gate checks pass (deterministic `pytest` + governance/doc sync validations).

If any row fails, the repository is not considered green for merge readiness.
