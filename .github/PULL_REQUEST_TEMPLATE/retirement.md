## Change type

- [ ] Wrapper retirement row
- [ ] Compatibility retirement row
- [ ] Retirement readiness evidence-only PR

## Issue link

Issue: ISSUE-XXXX

## Selected retirement row

- **Selected row:**
- **Why this row now (leverage consumed):**
- **Bounded authority slice in scope:**

## Current authority map

- **Current owner/path:**
- **Canonical runtime/control-point path:**
- **Compatibility delegation posture (if any):**

## Ideal future state

- **Target owner/path after retirement:**
- **What canonical path should no longer depend on:**
- **Outside scope in this PR:**

## Retirement-specific evidence requirements

### Caller census

- Evidence (in-repo callers + any known external compatibility callers):
- Claim supported by this evidence and why:
- Stronger claim not yet supported and why not:

### Semantic ownership census

- Evidence (who currently owns behavior semantics vs forwarding mechanics):
- Claim supported by this evidence and why:
- Stronger claim not yet supported and why not:

### Removal criteria checklist

- [ ] Canonical runtime path ownership is explicit for the behavior being retired.
- [ ] Compatibility delegation is explicitly bounded.
- [ ] Caller census supports retirement posture claimed.
- [ ] Anti-backslide guard exists (test/assertion/checklist) for the retired surface.
- [ ] Deferred category debt (if any) is explicitly named.

### Runtime equivalence or control-point proof

- Evidence (equivalence test, invariant check, or control-point assertions):
- Claim supported by this evidence and why:
- Stronger claim not yet supported and why not:

### Explicit retirement-finishability statement

- **Is retirement directly finishable now?**
- **If no, what specifically blocks retirement?**
- **What smallest change/evidence would make retirement directly finishable?**

## Implemented change

- **What was changed in this PR:**
- **Why this is a bounded retirement move (not broader redesign):**

## Strongest justified claim

- **Strongest bounded claim this PR justifies:**

## Remaining deferred scope

### Rows remaining

- 

### Category debt remaining

- 

## Options opened by this PR

For each option include:
- **What the option would do:**
- **What it depends on:**
- **Recommended next option and why:**

## How this PR makes later moves easier

- **Ambiguity reduced:**
- **Ownership boundary made clearer:**
- **What future move is now safer/smaller/faster:**

## Operational posture (lightweight)

- **Risk level (low / medium / high):**
- **Rollback posture:**
- **What to watch after merge:**

## PR-ready summary

- **Selected retirement row processed:**
- **Leverage consumed:**
- **Bounded authority moved (or readiness evidence hardened):**
- **Rows remaining + category debt remaining:**
- **Recommended next move:**

## Tests run

<!-- List exact commands and outcomes. -->
