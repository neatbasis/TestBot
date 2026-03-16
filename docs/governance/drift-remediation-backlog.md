# Drift Remediation Backlog

This backlog converts currently documented drift signals into sprintable remediation work, prioritized by governance and operational risk.

## Critical (policy/safety/red-tag)

### 1) Semantic self-identity routing regression remains open red-tag
- **Issue ID:** ISSUE-0014 (linked hardening tracker: ISSUE-0015)
- **Problem statement:** Self-identification turns can be semantically misrouted before retrieval/commit, creating correctness and safety risk in stakeholder-visible identity recall behavior.
- **Affected paths:**
  - `src/testbot/stage_rewrite_query.py`
  - `src/testbot/intent_resolution.py`
  - `src/testbot/policy_decision.py`
  - `src/testbot/answer_commit.py`
  - `features/testbot/intent_grounding.feature`
  - `features/testbot/memory_recall.feature`
  - `tests/test_intent_router.py`
  - `tests/test_answer_commit_identity_promotion.py`
- **Acceptance criteria:**
  1. Self-identification discourse type is preserved through rewrite + intent stages for representative identity turns.
  2. Retrieval is activated for continuity-anchored self-reference recall rather than defaulting to unsupported direct answers.
  3. Confirmed identity facts are promoted through `answer.commit` with deterministic assertions.
  4. ISSUE-0014/ISSUE-0015 status and RED_TAG index remain lifecycle-consistent.
- **Validation commands to run:**
  - `python -m behave`
  - `python -m pytest tests/test_intent_router.py tests/test_answer_commit_identity_promotion.py`
  - `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
  - `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
- **Estimated effort:** L
- **Target sprint:** Sprint N+1
- **Dependency notes:** Must complete before closing linked dependency milestones in ISSUE-0013 and before ISSUE-0015 can be resolved.

### 2) Canonical pipeline closure dependency guardrails must stay enforceable
- **Issue ID:** ISSUE-0015
- **Problem statement:** Governance can drift if dependency-chain closure rules (ISSUE-0013 ↔ ISSUE-0014 ↔ ISSUE-0015) are not continuously machine-validated, risking premature “green” signaling.
- **Affected paths:**
  - `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
  - `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
  - `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
  - `docs/issues/RED_TAG.md`
  - `scripts/validate_issue_links.py`
  - `scripts/validate_issues.py`
- **Acceptance criteria:**
  1. Dependency gating rules are explicitly reflected and non-contradictory across the three issue files and RED_TAG index.
  2. Validators fail when dependency lifecycle states become inconsistent.
  3. Evidence notes include deterministic command traces for lifecycle transitions.
- **Validation commands to run:**
  - `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
  - `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
  - `python scripts/all_green_gate.py`
- **Estimated effort:** M
- **Target sprint:** Sprint N+1
- **Dependency notes:** Blocked by unresolved functional exit conditions under ISSUE-0014 and ISSUE-0013.

## High (architecture contradictions with operational risk)

### 3) Re-center policy authority in canonical `policy.decide`
- **Issue ID:** ISSUE-0013
- **Problem statement:** Policy posture/branching decisions are split across stages, weakening architecture contract boundaries and increasing nondeterministic routing risk.
- **Affected paths:**
  - `src/testbot/canonical_turn_orchestrator.py`
  - `src/testbot/policy_decision.py`
  - `src/testbot/intent_resolution.py`
  - `docs/architecture.md`
  - `tests/test_pipeline_semantic_contracts.py`
- **Acceptance criteria:**
  1. Retrieval branch + policy posture are selected in `policy.decide` only.
  2. Pre-policy stages do not mutate authoritative policy artifacts.
  3. Regression tests verify no policy-authority leakage before `policy.decide`.
- **Validation commands to run:**
  - `python -m pytest tests/test_pipeline_semantic_contracts.py`
  - `python -m pytest tests/test_canonical_turn_orchestrator.py`
  - `python scripts/all_green_gate.py`
- **Estimated effort:** L
- **Target sprint:** Sprint N+1
- **Dependency notes:** Coordinate with ISSUE-0014 fixes to avoid reintroducing identity-routing regressions.

### 4) Separate answer stage side effects to restore canonical stage contracts
- **Issue ID:** ISSUE-0013
- **Problem statement:** `answer.assemble` currently performs validation/render/commit side effects via legacy helper flow, contradicting stage isolation guarantees.
- **Affected paths:**
  - `src/testbot/sat_chatbot_memory_v2.py`
  - `src/testbot/canonical_turn_orchestrator.py`
  - `src/testbot/answer_assemble.py`
  - `src/testbot/answer_validate.py`
  - `src/testbot/answer_render.py`
  - `src/testbot/answer_commit.py`
  - `tests/test_pipeline_semantic_contracts.py`
- **Acceptance criteria:**
  1. Each canonical answer stage mutates only its declared artifacts.
  2. No commit/validation/render side effects occur during `answer.assemble`.
  3. Stage contract tests fail on cross-stage side effects.
- **Validation commands to run:**
  - `python -m pytest tests/test_pipeline_semantic_contracts.py`
  - `python -m pytest tests/test_runtime_logging_events.py`
  - `python scripts/all_green_gate.py`
- **Estimated effort:** L
- **Target sprint:** Sprint N+2
- **Dependency notes:** Best sequenced after policy-authority consolidation to reduce refactor overlap.

## Medium (acceptance criteria mismatch)

### 5) Complete knowing-mode provenance coverage for open acceptance deltas
- **Issue ID:** ISSUE-0009
- **Problem statement:** Provenance/citation guardrails are partially distributed across legacy and canonical paths, leaving acceptance criteria at risk of partial enforcement.
- **Affected paths:**
  - `src/testbot/answer_validate.py`
  - `src/testbot/answer_render.py`
  - `features/testbot/answer_contract.feature`
  - `tests/test_eval_runtime_parity.py`
- **Acceptance criteria:**
  1. Canonical `answer.validate` enforces citation/provenance checks for factual outputs.
  2. Feature scenarios and deterministic tests cover pass/fail provenance cases.
  3. No contradiction remains between issue AC language and runtime validation behavior.
- **Validation commands to run:**
  - `python -m behave`
  - `python -m pytest tests/test_eval_runtime_parity.py`
  - `python scripts/all_green_gate.py`
- **Estimated effort:** M
- **Target sprint:** Sprint N+2
- **Dependency notes:** Depends on answer-stage isolation cleanup for clean ownership boundaries.

### 6) Complete unknowing-mode fallback contract for weak evidence cases
- **Issue ID:** ISSUE-0010
- **Problem statement:** Unknowing-mode fallback semantics can pass partially due to mixed enforcement layers, risking acceptance mismatch under ambiguous evidence.
- **Affected paths:**
  - `src/testbot/reflection_policy.py`
  - `src/testbot/policy_decision.py`
  - `src/testbot/answer_render.py`
  - `features/testbot/answer_contract.feature`
  - `tests/test_reflection_policy.py`
- **Acceptance criteria:**
  1. Weak/conflicting evidence deterministically yields explicit uncertainty + safe fallback.
  2. Fallback behavior is scenario-covered and assertion-complete in deterministic tests.
  3. Acceptance criteria in ISSUE-0010 map 1:1 to executable checks.
- **Validation commands to run:**
  - `python -m behave`
  - `python -m pytest tests/test_reflection_policy.py`
  - `python scripts/all_green_gate.py`
- **Estimated effort:** M
- **Target sprint:** Sprint N+2
- **Dependency notes:** Should be verified together with ISSUE-0009 to prevent policy divergence between knowing and unknowing modes.

## Low (documentation lag)

### 7) Keep architecture/governance drift artifacts synchronized after refactors
- **Issue ID:** ISSUE-0013 (documentation follow-through scope)
- **Problem statement:** Architecture and drift governance docs can lag after code fixes, reducing auditability and making future triage ambiguous.
- **Affected paths:**
  - `docs/architecture.md`
  - `docs/governance/architecture-drift-register.md`
  - `docs/governance/drift-traceability-matrix.md`
  - `docs/testing.md`
- **Acceptance criteria:**
  1. Drift findings marked remediated in code are reflected in governance artifacts in the same change set.
  2. Validation surfaces in drift matrix stay aligned with actual tests/features.
  3. No stale contradiction remains between architecture narrative and runtime implementation.
- **Validation commands to run:**
  - `python scripts/all_green_gate.py --continue-on-failure`
  - `python -m pytest tests/test_validate_markdown_paths.py`
- **Estimated effort:** S
- **Target sprint:** Sprint N+3
- **Dependency notes:** Triggered incrementally as higher-priority implementation items land.

### 8) Close startup degraded-mode BDD traceability gap
- **Issue ID:** ISSUE-0016
- **Problem statement:** Startup degraded-mode behavior is tested in pytest but lacks explicit feature-level BDD articulation, creating readability and traceability lag.
- **Affected paths:**
  - `features/testbot/capabilities.feature` (or new startup-focused feature file)
  - `features/steps/`
  - `tests/test_startup_status.py`
  - `tests/test_runtime_modes.py`
  - `docs/governance/mission-vision-alignment.md`
- **Acceptance criteria:**
  1. Startup degraded-mode messaging has explicit BDD scenarios.
  2. Deterministic tests align with new scenario branches.
  3. Governance alignment doc marks the gap as closed with references.
- **Validation commands to run:**
  - `python -m behave`
  - `python -m pytest -m "not live_smoke"`
  - `python scripts/all_green_gate.py`
- **Estimated effort:** S
- **Target sprint:** Sprint N+3
- **Dependency notes:** Independent item; can be executed in parallel with medium-priority acceptance alignment work.
