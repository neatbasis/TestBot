# ISSUE-0022 cleanup workstream execution slice #1 (stale ownership/sequence framing)

- **Issue:** ISSUE-0022
- **Date:** 2026-03-29
- **Unit type:** cleanup workstream execution slice
- **Scope type:** bounded docs/evidence cleanup (no runtime/scorer behavior change)
- **Truth anchors:**
  - `docs/issues/evidence/2026-03-29-issue-0022-progress-and-landing-review.md`
  - `docs/issues/evidence/2026-03-29-issue-0022-cleanup-and-behave-catchup-meta-program.md`

## 1) Cleanup inventory (selected bounded slice)

This slice targets stale assumptions that can cause authority drift during follow-on PRs:

1. **Stale sequencing assumption**
   - stale reference: post-landing artifacts that still read like “next immediate move = scorer candidate-output seam,”
   - risk: reviewers can skip cleanup/behave sequencing and reintroduce stale ownership language while executing scorer work.

2. **Stale ownership framing assumption**
   - stale reference: handoff notes that do not explicitly distinguish immediate ambient cleanup workstream from later scorer-category execution,
   - risk: ambient debt can be misread as scorer debt, blurring row/category and seam/debt boundaries.

3. **Stale intermediate-state framing**
   - stale reference: pre-#703 wording remains accurate about scorer seam ordering, but outdated about *execution order* after the meta split,
   - risk: evidence notes drift from canonical landing-state + meta program control flow.

## 2) Implemented cleanup updates

### A) Landing-state review sequencing normalization

Updated `2026-03-29-issue-0022-progress-and-landing-review.md` so section 5 now:

- names **cleanup workstream first** and **behave catch-up second** as immediate moves,
- keeps candidate-output/projection shaping as the **next scorer-category move after those streams**,
- clarifies this is sequencing safety, not scorer-semantic change.

### B) ISSUE-0022 inventory handoff wording normalization

Updated `ISSUE-0022-residual-runtime-helper-authority-inventory-after-loop-owner-extraction.md` to:

- relabel “recommended next smallest scorer-internals slice” as a **post-cleanup/post-behave scorer move**,
- add a #703 sequencing addendum that codifies cleanup → behave catch-up → scorer seam,
- explicitly state no scorer-semantic changes are implied by this cleanup.

## 3) Before/after stale-assumption map

- **Before:** candidate-output/projection seam read as immediate next execution move.
- **After:** candidate-output/projection seam is preserved as next scorer-category move, but only after cleanup then behave catch-up.

- **Before:** handoff text could be read as scorer-category-first while ambient debt remained implicit.
- **After:** ambient cleanup and behave catch-up are explicit first-class workstreams with ordered execution.

## 4) Evidence statements

- Evidence X supports claim Y because Z: the #703 meta artifact explicitly defines cleanup-first and behave-catch-up-second sequencing, so updating landing/handoff wording to match that sequence prevents stale execution assumptions.
- It does not yet support stronger claim W because Q: wording cleanup does not itself resolve behave failures or execute the next scorer seam; those require separate bounded PRs.

- Evidence X supports claim Y because Z: retaining candidate-output/projection as the next scorer-category seam preserves category-debt truth while preventing authority drift from stale “immediate-next” phrasing.
- It does not yet support stronger claim W because Q: this cleanup does not provide new scorer control-point evidence or semantic parity proof for that seam.

## 5) Strongest justified claim

A bounded cleanup slice has removed stale sequencing/ownership wording that could misframe ISSUE-0022 follow-on execution, while preserving the canonical landing-state truth: row program complete, scorer-category debt active, and candidate-output/projection seam still next in scorer queue after cleanup and behave catch-up.

## 6) Out of scope (explicit)

- No behave scenario edits.
- No scorer-category code extraction.
- No architecture redesign.
- No change to runtime/scorer semantics.

## 7) Validation commands run

- `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
- `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
