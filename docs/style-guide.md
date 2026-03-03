# Documentation Style Guide

Use this guide for all docs in this repository (`README.md`, `docs/*.md`, and `features/README.md`).

## Writing rules

### 1) Clear

- Use plain language and avoid jargon when a simpler term works.
- Define acronyms the first time they appear, then reuse the same acronym.
- Prefer concrete statements over vague guidance.

### 2) Concise

- Keep sections short and focused on one idea.
- Remove duplicate guidance; link to the canonical section instead of repeating it.
- Use bullets and checklists for scan-friendly instructions.

### 3) Consistent

- Use one canonical term per concept across all docs.
- For the fallback behavior, always use **"memory-grounded fallback"** as the canonical term.
- Keep heading structure and phrasing patterns consistent between docs.

## Make implicit domain assumptions explicit

When a docs update relies on tacit engineering or governance knowledge, write those assumptions down instead of leaving them implied.

Include the following when relevant:

- **Quality model assumptions** (for example: BDD-first for stakeholder-visible behavior, deterministic fixtures for reproducibility).
- **Risk model assumptions** (for example: docs drift, terminology drift, command rot, link rot).
- **Governance assumptions** (for example: Definition of Done gates, milestone/release review cadence, role ownership).
- **Architecture assumptions** (for example: retrieval/rerank pipeline invariants and where they are enforced).

For high-impact docs changes, add an explicit subsection named `Assumptions and invariants`.

## Required questions for every new docs section

Every newly added section must explicitly answer:

1. **Who is this for?**
2. **What action/decision does it support?**
3. **When should this be used?**
4. **Where in repo/runtime does it apply?**
5. **Why does it matter?**

## Docs drift checks

Before merging docs changes, verify:

- Repository layout examples match the actual files and folders in the repo.
- Commands are runnable exactly as written.
- Cross-links to docs/features resolve to valid paths.

## Review cadence

Run a docs review at least once per milestone or release, and whenever major architecture or workflow changes land.

## Optional maturity add-ons (when scope warrants)

If a change introduces or modifies core behavior contracts, also consider:

- A lightweight **risk mapping** note (what can drift/fail, how it is detected).
- A **traceability map** from behavior contract → test/feature files → operational checks.
- A short **invariant registry** section for non-negotiable system truths.
