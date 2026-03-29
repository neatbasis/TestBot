# ISSUE-0022 cleanup + behave catch-up meta follow-up program (post-landing-state anchor)

- **Issue:** ISSUE-0022
- **Date:** 2026-03-29
- **Artifact type:** bounded docs/process meta PR control artifact (planning + risk controls only)
- **Landing-state anchor:** `docs/issues/evidence/2026-03-29-issue-0022-progress-and-landing-review.md` (post-#701)

## 1) Meta PR scope

This meta artifact defines two explicit follow-up workstreams after the current ISSUE-0022 landing state:

1. **cleanup workstream** (stale assumptions/wording/evidence references), and
2. **behave catch-up workstream** (validation scenarios/gate alignment to current ownership boundaries).

What this PR prepares:

- bounded scopes,
- phase-aware sequencing,
- regression-risk controls,
- completion evidence expectations for follow-on execution PRs.

What this PR deliberately does **not** execute:

- broad file cleanup,
- broad behave scenario rewrites,
- scorer-category seam extraction/redesign,
- broad architecture rewrite beyond this canonical planning/control artifact.

- Evidence X supports claim Y because Z: the landing-state anchor already separates bounded scorer-category seams from ambient repo debt (including behave/gate drift and stale assumptions), so creating explicit follow-up workstreams is now the smallest non-regressive organizing move.
- It does not yet support stronger claim W because Q: the anchor identifies the debt classes and recommended seam sequencing, but it does not itself perform cleanup execution or validation catch-up remediation.

## 2) Why these workstreams now matter

Cleanup and behave catch-up are first-class now because the landing-state anchor has already clarified:

- what is complete (wrapper-retirement phase complete; selected scorer-category seams complete),
- what remains as scorer-category seam debt,
- what remains as ambient repo debt,
- and where current ownership boundaries now live.

This means ambiguity reduction has reached the point where stale language and stale validation assumptions now create **authority drift risk** rather than harmless documentation lag.

- Evidence X supports claim Y because Z: the anchor explicitly reports split-authority landing state plus ambient behave/gate instability, so stale wording/tests can now misrepresent current ownership if left unmanaged.
- It does not yet support stronger claim W because Q: the anchor does not prove every stale reference location or every obsolete scenario already cataloged; follow-on execution PRs must inventory/update concretely.

## 3) Cleanup workstream

### Purpose

Eliminate stale wording, stale assumptions, and stale evidence-note guidance that no longer matches the post-#700/#701 landing state and current authority boundaries.

### Why needed now

Now that boundary ownership has materially shifted, stale references can obscure canonical authority and increase reviewer confusion during subsequent bounded scorer work.

### In scope

- stale terminology that implies retired wrapper-row ownership still active,
- stale references that treat completed row-program work as pending,
- stale evidence-note recommendations that predate current landing-state decisions,
- stale assumptions about authority location after seam/category moves,
- narrow updates to docs/process artifacts so they point to current canonical anchors.

### Out of scope

- changing runtime/scorer behavior,
- executing new scorer-category seam extraction,
- re-architecting scoring internals,
- broad editorial rewrites unrelated to authority drift prevention.

### Expected deliverables

- one bounded cleanup PR (or small sequence) with a curated stale-reference inventory,
- targeted doc edits that normalize wording to current landing-state anchor,
- explicit before/after mapping for renamed ownership assumptions,
- updated evidence-note recommendations that reflect current deferred seam vs ambient debt split.

### Completion evidence

- stale-reference checklist with each item marked resolved/deferred-with-rationale,
- validators pass (`validate_issue_links.py`, `validate_issues.py`) on changed issue/docs artifacts,
- explicit statement that cleanup did not modify scorer semantics,
- reviewer-visible proof that canonical authority pointers are consistent post-cleanup.

- Evidence X supports claim Y because Z: the anchor calls out stale-supporting-artifact assumptions as ambient debt and recommends keeping seam execution separate, so a dedicated cleanup workstream is directly justified.
- It does not yet support stronger claim W because Q: naming cleanup as a stream does not itself guarantee all stale references are found; the follow-on cleanup PR must provide concrete inventory evidence.

## 4) Behave catch-up workstream

### Purpose

Bring behave scenarios and gate expectations into alignment with current ownership boundaries while preserving behavioral intent.

### Why needed now

Broad gate health still reports pre-existing behave failures unrelated to the landing-state review docs PR, which means validation currently lags reality and can produce misleading failure signals.

### In scope

- scenarios encoding obsolete monolith/wrapper ownership assumptions,
- scenario expectations that conflict with current runtime/control-point ownership boundaries,
- step or expectation updates needed to preserve intent while matching current authority model,
- explicit separation of slice-specific evidence from broad gate health when reporting progress.

### Out of scope

- scorer redesign and new scoring policy behavior,
- changing product intent contracts to “make tests green,”
- broad non-behave test-suite redesign,
- conflating behave catch-up with new seam extraction execution.

### Expected deliverables

- one bounded behave catch-up PR (or staged subset PRs) with scenario inventory + classification,
- scenario updates that keep intent stable while removing obsolete ownership assumptions,
- gate-readiness notes distinguishing workstream-local scenario progress from repo-wide gate state,
- explicit mapping from updated scenarios to current seam/control-point sources of truth.

### Completion evidence

- inventory of touched scenarios with old assumption → new authority mapping,
- explicit confirmation that behavioral intent is preserved,
- canonical gate/behave command outputs attached with failure attribution clarity,
- documented residual failures (if any) outside updated scope with next-step notes.

- Evidence X supports claim Y because Z: the anchor explicitly records pre-existing behave/gate failure context unrelated to the docs-only landing review, so a separate behave catch-up stream is necessary to restore validation signal quality.
- It does not yet support stronger claim W because Q: anchor-level failure attribution does not identify every failing scenario’s root cause; catch-up execution must still perform scenario-by-scenario reconciliation.

## 5) Recommended sequence (safe sequencing)

**Recommended order:**

1. **cleanup workstream first**,
2. **behave catch-up workstream second**.

Why this sequence is safest:

- cleanup first reduces terminology/authority ambiguity so behave updates reference stable, current language,
- behave catch-up second then updates validation against clarified authority targets,
- this lowers risk of re-encoding obsolete assumptions into new scenarios while catch-up is underway.

- Evidence X supports claim Y because Z: the landing-state anchor separates ambient stale-artifact debt from scorer-category seam debt and flags behave drift as ambient instability, so clearing stale authority wording first reduces interpretation noise before test-expectation updates.
- It does not yet support stronger claim W because Q: sequence guidance alone does not eliminate hidden coupling; each follow-on PR must still provide bounded diff and regression controls.

## 6) Regression-risk controls (authority drift prevention)

All follow-on PRs under this meta program should enforce these controls:

1. **Preserve behavioral intent**
   - Update scenario/doc wording to match ownership reality without changing product intent contracts.
2. **Do not reintroduce obsolete monolith/wrapper ownership assumptions**
   - Any residual compatibility references must be explicit shim posture, not restored authority claims.
3. **Use current seam/control-point artifacts as source of truth**
   - Ground updates in the landing-state anchor and linked seam evidence, not pre-landing assumptions.
4. **Distinguish slice-specific evidence from broad gate health**
   - Report local stream progress separately from repo-wide all-green status.
5. **Avoid silent scope broadening into scorer redesign**
   - If a change appears to require scorer internals redesign, stop and open separate bounded seam/scorer planning.
6. **Bounded-diff discipline**
   - Keep each follow-on PR narrow, with explicit in-scope/out-of-scope statement and residual debt note.

- Evidence X supports claim Y because Z: the anchor frames remaining scorer-category seams, broad redesign deferrals, and ambient debt as distinct classes, so these controls directly prevent class-mixing regressions.
- It does not yet support stronger claim W because Q: controls are policy-level until enforced by PR review discipline and concrete follow-on evidence.

## 7) How these workstreams support later scorer work

This meta program supports later bounded scorer-category PRs by:

- reducing authority-language ambiguity before additional seam extraction,
- improving validation trustworthiness so scorer PR signal is easier to interpret,
- preventing ambient cleanup and validation drift from contaminating scorer-slice review scope,
- preserving the landing-state anchor as the canonical planning baseline.

- Evidence X supports claim Y because Z: the anchor already identifies one next bounded scorer seam and separates ambient debt; resolving ambient debt streams in controlled order improves clarity for future scorer-slice decisions.
- It does not yet support stronger claim W because Q: this meta artifact does not itself deliver scorer-category seam closure or complete gate health restoration.

## 8) What remains out of scope

This meta PR does not attempt to execute:

- cleanup implementation across broad docs corpus,
- behave failure remediation across the full suite,
- scorer-category seam extraction beyond current landing-state recommendation,
- objective/fusion/coefficient redesign or other broad scorer algorithm changes.

## 9) Implemented docs/process change

- Added one canonical meta planning/control artifact:
  - `docs/issues/evidence/2026-03-29-issue-0022-cleanup-and-behave-catchup-meta-program.md`
- No runtime/scorer behavior changes in this PR.

## 10) Strongest justified claim

The strongest bounded claim this meta PR supports is:

> After the ISSUE-0022 landing-state anchor, cleanup debt and behave/gate catch-up debt are now explicitly separated into two safe, bounded follow-up workstreams with recommended sequencing and regression-risk controls, enabling non-regressive preparation for later scorer-category execution PRs.

## 11) PR-ready summary

This meta artifact turns post-landing ambient debt into an explicit follow-up program: a first cleanup workstream for stale authority wording/references, then a behave catch-up workstream for validation alignment to current ownership boundaries. It keeps scorer-category redesign out of scope, adds authority drift prevention controls, and defines completion evidence so each follow-on PR remains bounded, reviewable, and non-regressive.

## 12) Tests / validation run

- `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
- `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
- `python scripts/all_green_gate.py` *(expected to surface pre-existing broad gate/behave failures outside this docs/process meta change scope)*
