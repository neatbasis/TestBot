# PR #682 post-merge deferred inventory and leverage note

- **Date:** 2026-03-29
- **Related Issue:** ISSUE-0022
- **Related PR:** [#682](https://github.com/neatbasis/TestBot/pull/682)
- **Scope:** post-merge inventory for deferred surfaces and leverage now available after runtime-facing context/retrieval seam extraction.

## What PR #682 bought

PR #682 moved runtime-facing context/retrieval hook wiring to a canonical runtime-owned service and rewired
`entrypoints/runtime_loop.py` to source seam hooks from that owner. This raised confidence that the canonical
runtime loop now owns the hook-binding surface for this seam, while preserving behavior via compatibility
wrappers.

Owned surfaces captured by the change:

- identity-recall forced-retrieval helper wiring;
- retrieval input/document conversion adapters;
- turn-service retrieve/rerank adapter wiring;
- runtime loop hook-binding control point for the seam.

## Deferred items inventory

### 1) Retrieval policy-core remains in legacy monolith

- **Deferred item:** `stage_retrieve` policy-core extraction out of `sat_chatbot_memory_v2`.
- **Why deferred:** PR #682 extracted runtime seam wiring/adapters, not deep retrieval decision semantics.
- **Implication:** runtime loop no longer depends on monolith helper ownership for this seam binding, but
  retrieval semantic ownership remains legacy for now.

### 2) Rerank / temporal policy-core remains in legacy monolith

- **Deferred item:** `stage_rerank` and coupled rerank/temporal policy-core extraction.
- **Why deferred:** scope preserved behavior by routing through canonical adapters while retaining legacy
  semantic internals.
- **Implication:** canonical control point now exists, but semantic authority is still legacy-owned.

### 3) `resolve_context` semantic ownership still needs full audit

- **Deferred item:** full semantic ownership audit for `resolve_context` and downstream assumptions.
- **Why deferred:** current evidence proves runtime hook binding ownership concentration, not full semantic
  migration finality.
- **Implication:** seam is now visible/governable, but deeper semantic boundaries may still need refinement.

### 4) Monolith retirement is still partial

- **Deferred item:** additional retirement of `sat_chatbot_memory_v2` as runtime authority holder.
- **Why deferred:** this increment intentionally used compatibility delegation rather than broad removal.
- **Implication:** monolith authority is reduced, but not yet collapsed to a minimal temporary shell.

### 5) Full all-green gate remains blocked outside this seam

- **Deferred item:** broader `behave` feature-suite failures unrelated to this seam extraction.
- **Why deferred:** pre-existing failures were not introduced by #682 and were outside narrow seam scope.
- **Implication:** seam step can still be validly merged with targeted evidence while broader readiness debt
  remains tracked separately.

## Leverage now available

### 1) Control-point leverage

With `runtime_loop.py` sourcing this seam from a canonical runtime-owned service, follow-on work can target one
hook-binding surface. This simplifies extraction sequencing and ownership assertion hardening.

### 2) Anti-backslide leverage

Strengthened runtime ownership assertions, compatibility-wrapper tests, and narrowed monolith allowlists convert
architecture intent into CI-enforced posture.

### 3) Compatibility leverage

Thin delegation shims preserve behavior while authority shifts. This supports staged extraction and avoids risky
big-bang rewrites.

### 4) Explanation leverage

PR #682 established explicit language for what moved, what did not move, and which residual surfaces are deferred.
That pattern improves review quality and claim precision for follow-on PRs.

### 5) Future-extraction leverage

The seam is now decomposed into concrete sub-surfaces (forced-retrieval helper, conversion, retrieve/rerank
adapters, runtime binding), enabling narrower and more deterministic next increments.

## Best next deltas (ordered by leverage)

1. **Extract retrieval policy-core behind canonical seam** (highest value next move).
2. **Extract rerank/temporal policy-core** (adjacent seam with similar mechanics).
3. **Tighten wrapper downgrade posture** (shrink allowlists, define removal/expiry criteria).
4. **Template this seam extraction pattern** (inventory, canonical owner, rewiring, wrappers, anti-backslide,
   explicit deferred scope).

## Compact state table

| Area | Current state after #682 | Deferred item | Leverage now available |
| --- | --- | --- | --- |
| Runtime hook binding | Canonical runtime-owned control surface | none for this seam-binding step | direct control-point leverage |
| Identity recall / conversion / adapters | Canonical service owns runtime-facing seam | deeper semantic ownership around downstream policy use | extraction pattern leverage |
| Retrieval | adapter path canonicalized | policy-core still legacy | next high-value extraction target |
| Rerank | adapter path canonicalized | rerank/temporal policy-core still legacy | adjacent extraction target |
| Context resolution | runtime sourcing canonicalized | deeper semantic ownership may still need refinement | better seam visibility |
| Monolith authority | reduced, not retired | further downgrade/removal | anti-backslide + allowlist leverage |
| Test posture | targeted seam evidence strong | broader behave failures remain elsewhere | safer narrow merges |

## Strongest summary

- **Deferred:** retrieval policy-core; rerank/temporal policy-core; deeper `resolve_context` semantic ownership
  audit; further monolith retirement; broader feature-suite readiness debt.
- **Leverage gained:** one canonical runtime hook control point; stronger anti-backslide assertions;
  behavior-preserving staged extraction path; clearer review language; reusable seam-extraction pattern.
- **Best next move:** use the canonical runtime seam to extract retrieval policy-core authority out of monolith
  ownership using the same bounded-scope + anti-backslide evidence posture.
