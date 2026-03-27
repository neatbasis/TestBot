# Governance Authority Remediation Plan

## Goal

Eliminate governance authority fragmentation by converging each rule family to one owner,
while keeping generated implementation docs descriptive only.

## Phased remedy

### Phase 1: Authority declaration and contract locking

- Maintain the curated governance authority map.
- Ensure every active rule family has a single owner declaration and listed consumers.
- Add/maintain deterministic tests that fail if key ownership boundaries drift.

### Phase 2: Shared policy extraction where needed

- Keep high-level policy primitives in shared modules.
- Keep validator scripts focused on domain-specific scanning/enforcement.
- Prevent duplicate semantic implementations by routing shared checks through owner primitives.

### Phase 3: Producer/consumer contract hardening

- Keep verification manifest schema authority centralized.
- Ensure producer and consumer share one contract module.
- Add round-trip tests to enforce parity.

### Phase 4: Publication and review hygiene

- Use mkdocstrings-generated API pages for code-level behavior visibility.
- Keep curated governance/architecture pages as the normative control narrative.
- Keep CI/local documentation check strict via `mkdocs build --strict`.

## Non-goals

- Generated API pages are not the canonical governance authority ledger.
- This plan does not replace issue workflow/state policy artifacts.
