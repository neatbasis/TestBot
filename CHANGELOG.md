# Changelog

## Entry template (use for every PR/refactor step)
For each changelog entry, answer these three questions explicitly:

1. **What moved, and where did it land?**
   - Include the old path/symbol, new path/symbol, and whether a delegation shim remains.
2. **What did not change?**
   - State verified non-changes (behavior, public API, wire protocol, session log schema, etc.).
3. **Why this step was taken in this order?**
   - One sentence describing sequencing rationale (dependency order, receiver-first, ambiguity reduction before next extraction, etc.).

## 2026-03-19

### 1) What moved, and where did it land?
- **Old path/symbol:** local helper `_is_definitional_query_form(...)` defined and called in `src/testbot/sat_chatbot_memory_v2.py`.
- **New path/symbol:** shared helper `is_definitional_query_form(...)` from `testbot.retrieval_routing` (imported and used by `sat_chatbot_memory_v2.py`).
- **Delegation shim:** none left behind; the local helper was removed.

### 2) What did not change?
- Definitional-query classification behavior did not intentionally change; this step is a mechanical de-duplication to use the existing canonical helper implementation.
- Public runtime entrypoints and external wire/session-log contracts were not modified by this step.

### 3) Why this step was taken in this order?
- Centralizing call sites onto the canonical retrieval-routing helper first removes ambiguity and drift risk before any further routing or intent-confidence refactors.
