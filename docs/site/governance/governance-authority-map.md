# Governance Authority Map (Canonical Curated Artifact)

> **Normative status:** This file is the explicit governance authority ledger.
> Generated API documentation is descriptive and must not replace authority declarations.

## Purpose

Define one canonical owner per governance rule family and make consumer boundaries explicit.
This prevents split authority across validators, gate orchestration, and documentation.

## Authority map

| Rule family | Canonical owner | Consumers | Enforcement entrypoint(s) | Primary tests | Notes |
| --- | --- | --- | --- | --- | --- |
| Non-trivial metadata must include ISSUE reference | `scripts/governance_rules.py` (`metadata_missing_issue_reference`) | `scripts/validate_issues.py`, `scripts/validate_issue_links.py` | `scripts/validate_issues.py`, `scripts/validate_issue_links.py`, `scripts/all_green_gate.py` (readiness profile) | `tests/test_governance_rules.py`, `tests/test_validate_issue_links.py`, `tests/test_validate_issues.py` | Shared primitive; validators consume without redefining decision semantics. |
| Canonical issue sections parsing/presence primitive | `scripts/governance_rules.py` (`parse_canonical_sections`, `missing_canonical_sections`) | `scripts/validate_issues.py`, `scripts/validate_issue_links.py` | same as above | `tests/test_governance_rules.py`, validator test suites | Shared primitive contract only; issue-state policy remains owner-specific in validator. |
| Issue state/status transition policy | `scripts/validate_issues.py` | `scripts/all_green_gate.py` (as runner only) | `scripts/validate_issues.py` | `tests/test_validate_issues.py` | Owner defines lifecycle matrix and transition constraints. |
| Commit traceability base-ref fail-closed behavior | `scripts/validate_issue_links.py` + `scripts/governance_base_ref.py` | `scripts/all_green_gate.py` (passes base ref), developer workflows | `scripts/validate_issue_links.py` | `tests/test_base_ref_policy_split.py`, `tests/test_validate_issue_links.py`, `tests/test_governance_base_ref_helper.py` | Commit traceability semantics remain strict by default unless explicit degraded mode is requested. |
| Verification manifest payload contract | `scripts/verification_manifest_contract.py` | `scripts/all_green_gate.py` (producer), `scripts/validate_issue_links.py` (consumer) | `scripts/all_green_gate.py`, `scripts/validate_issue_links.py` | `tests/test_verification_manifest_contract.py`, `tests/test_validate_issue_links.py`, `tests/test_all_green_gate.py` | Single schema/required-check contract for producer and consumer parity. |
| Readiness/triage gate orchestration and skip policy | `scripts/all_green_gate.py` | CI workflows, local developers | `scripts/all_green_gate.py` | `tests/test_all_green_gate.py` | Gate orchestrates checks and skip policy; validator internals remain out of scope. |

## Operating constraints

1. Exactly one canonical owner per rule family.
2. Consumers may call owner utilities but must not silently fork equivalent semantics.
3. Any ownership transfer requires synchronized updates across this map, implementation, and deterministic tests.
4. Generated API docs may explain behavior but cannot become normative ownership records.

## Update protocol

When a governance rule changes:

1. Update this map first.
2. Update owner implementation and consuming callers.
3. Update deterministic tests that prove the boundary.
4. Run canonical readiness validation (`python scripts/all_green_gate.py`).
