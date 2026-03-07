# Production debug evidence: CLI trace mapped to ISSUE-0009/ISSUE-0010 acceptance criteria (2026-03-07)

## Purpose
Capture an exact local production-debug CLI trace and map each observed symptom to the active acceptance criteria in:
- `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`

## Exact CLI trace

### 1) Canonical gate execution
```bash
python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json
```

Observed terminal output (verbatim excerpts):

```text
Failing scenarios:
  features/memory_recall.feature:22  equivalent candidates remain ambiguous after tie-break
```

```text
FAILED tests/test_alignment_transitions.py::test_stage_answer_memory_hit_without_ambiguity_does_not_force_clarifier_mode
E       assert 'From memory,...-01T00:00:00Z' == "I don't have...ssing detail."
```

```text
{
  "status": "failed",
  "exit_code": 1,
  "continue_on_failure": true,
  "warning_count": 1,
  "checks": [
    {"name": "product_behave", "status": "failed"},
    {"name": "safety_behave_answer_contract_and_memory", "status": "failed"},
    {"name": "qa_pytest_not_live_smoke", "status": "failed"},
    {"name": "qa_validate_kpi_guardrails", "status": "warning"}
  ]
}
```

### 2) ISSUE-0009 acceptance-criteria targeted checks
```bash
python -m behave features/answer_contract.feature features/memory_recall.feature
```

```text
Failing scenarios:
  features/memory_recall.feature:22  equivalent candidates remain ambiguous after tie-break
```

```bash
python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py
```

```text
============================== 24 passed in 2.25s ==============================
```

### 3) ISSUE-0010 acceptance-criteria targeted checks
```bash
python -m behave features/answer_contract.feature features/intent_grounding.feature
```

```text
2 features passed, 0 failed, 0 skipped
19 scenarios passed, 0 failed, 0 skipped
```

```bash
python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py
```

```text
============================== 40 passed in 2.35s ==============================
```

## Symptom-to-acceptance-criteria mapping

| Symptom from trace | Issue + Acceptance Criterion | Mapping result |
|---|---|---|
| `features/memory_recall.feature:22 equivalent candidates remain ambiguous after tie-break` fails | ISSUE-0009 AC1 (`behave features/answer_contract.feature features/memory_recall.feature` must pass) | **Not met** |
| Gate summary shows `safety_behave_answer_contract_and_memory` failed | ISSUE-0009 AC3 (`safety_behave_answer_contract_and_memory` must be `passed`) | **Not met** |
| `qa_pytest_not_live_smoke` fails due to `test_stage_answer_memory_hit_without_ambiguity_does_not_force_clarifier_mode` expectation mismatch | ISSUE-0009 AC3 cross-check consistency (overall gate evidence) | **Not met / drift signal** |
| `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py` passes | ISSUE-0009 AC2 | **Met** |
| `python -m behave features/answer_contract.feature features/intent_grounding.feature` passes | ISSUE-0010 AC1 | **Met** |
| `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py` passes | ISSUE-0010 AC2 | **Met** |
| Gate summary shows `product_behave` failed | ISSUE-0010 AC3 (`product_behave` and `safety_reflection_and_runtime_logging_pytests` must be `passed`) | **Not met** |

## Delta notes for current partial status

1. **Confident memory-recall recovery remains open**: ambiguity/tie-break scenario is still failing in BDD and blocks ISSUE-0009 AC1/AC3.
2. **Citation-context format remains open**: known cross-test expectation drift indicates citation-context shape/branch output is not yet fully aligned across memory-hit and fallback paths.
3. **Debug reason accuracy remains open**: acceptance closure still requires reason strings in runtime/debug traces to match actual branch outcomes, especially across confidence, ambiguity, and fallback transitions.

## Reporting/status artifacts
Per issue instructions, status artifact regeneration via report scripts is deferred until criteria are implemented and validated as passing.

ISSUE-0013 linkage: Canonical pipeline progress and defect-elimination sequencing for this evidence are tracked under ISSUE-0013.
