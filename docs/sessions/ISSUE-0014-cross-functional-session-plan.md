# ISSUE-0014 Cross-Functional Session Plan (90-120 minutes)

- **Issue:** ISSUE-0014
- **Session objective:** Confirm root cause and finalize containment + permanent corrective plan for CLI identity declaration and self-reference recall regression.
- **Participants required:**
  - platform-qa
  - runtime/pipeline engineering
  - test/BDD ownership
  - release governance

## Pre-Read and Artifact Packet (D0 input)

Required materials:

1. `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
2. `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
3. `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
4. `docs/issues/evidence/production-debug-cli-session-log-2026-03-08-21-23.jsonl`

## Agenda and Timebox

### D0 (Plan) - 10 min
- Confirm scope: identity declaration + self-reference recall regression in CLI canonical pipeline.
- Confirm session goals:
  - root cause confirmation,
  - interim containment,
  - permanent corrective actions,
  - verification/traceability plan.

### D1 (Team) - 10 min
- Confirm role assignments:
  - Facilitator
  - Scribe
  - Rewrite owner
  - Intent/routing owner
  - Commit/persistence owner
  - Test/BDD owner
- Capture owner matrix in issue update before moving to D2.

### D2 (Problem Description) - 15 min
- Build 5W2H using exact reproducer:
  - Turn 1: `Hi! I'm sebastian`
  - Turn 2: `Who am I?`
- Stage-by-stage observed vs expected walkthrough:
  - rewrite
  - intent
  - branch selection
  - retrieval/rerank
  - commit promotion
  - response

### D3 (Interim Containment) - 10 min
- Approve immediate safeguards:
  - temporary rewrite bypass/guard for identity declarations,
  - temporary routing guard to block direct-answer shortcut for self-referential identity recall with continuity markers.
- Require deterministic regression tests to ship with containment.

### D4 (Root Cause Analysis) - 15 min
- Validate evidence-led fault tree:
  1. semantic inversion in rewrite,
  2. intent/context weighting deficit,
  3. premature direct-answer routing,
  4. commit promotion gap.
- Confirm chain with trace checkpoints and deterministic reproductions.

### D5 (Permanent Corrective Actions) - 15 min
- Approve permanent changes for:
  - rewrite invariance for identity declarations,
  - continuity-aware intent/routing,
  - branch guard for self-reference memory recall,
  - durable identity fact promotion.
- Map each action to owner and target files in:
  - `src/testbot/`
  - `features/`
  - `tests/`

### D6 (Implement & Validate) - 15 min
- Validation gate commitments:
  - `python -m behave features/testbot/memory_recall.feature features/testbot/intent_grounding.feature`
  - `python -m pytest -m "not live_smoke"`
  - `python scripts/all_green_gate.py`
- Require explicit AC traceability from ISSUE-0014 acceptance criteria to test names and outputs.

### D7 (Prevent Recurrence) - 10 min
- Plan permanent regression suite for identity declaration/recall continuity.
- Add invariant checks for rewrite discourse-type preservation and route/evidence coherence.
- Update governance artifacts as needed (`docs/directives/`, issue links, status reporting).

### D8 (Closure & Recognition) - 5 min
- Closure criteria:
  - ISSUE-0014 ACs fully met,
  - gate evidence attached,
  - no unresolved contradiction between docs/runtime/tests.
- Record lessons learned and route taxonomy updates in issue notes.
- Acknowledge contributors and publish Sprint 6 postmortem summary.

## Outputs Required by End of Session

1. Updated owner matrix recorded on ISSUE-0014.
2. 5W2H problem statement with stage-wise observed vs expected table.
3. Containment decision log with required tests.
4. Fault-tree confirmation with trace checkpoints.
5. Permanent corrective action plan mapped to code owners + files.
6. Verification plan with command outputs and AC traceability matrix.
7. Recurrence prevention updates (regression + invariants + governance updates).
8. Closure note template ready for Sprint 6 postmortem publication.
