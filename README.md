# TestBot

## What
TestBot is a stateful, retrieval-augmented conversational agent with persistent memory and multi-interface interaction.

### Terminology (ontology crosswalk)
- **turn pipeline** → agent inference pipeline
- **memory cards** → episodic memory store
- **vector store retrieval** → retrieval-augmented generation (RAG)
- **durable facts** → persistent memory / long-term memory
- **CLI / satellite** → interaction interfaces
- **structured logs** → telemetry / observability
- **context resolution** → context management
- **commit stage** → memory update / memory consolidation

Internal names remain canonical identifiers; standard terms are provided for wider community readability.
See [docs/terminology.md](docs/terminology.md) for the canonical terminology policy, including rules for combining internal identifiers with standard AI terms.

### Cognitive architecture alignment
TestBot's pipeline mirrors a perception → memory → reasoning → action model:

| Cognitive architecture | TestBot concept |
| --- | --- |
| perception | observe stage |
| encoding | encode stage |
| working memory | canonical state |
| episodic memory | vector store |
| reasoning | inference |
| action | answer generation |
| learning | commit stage |

## Vision
TestBot is a user-steered assistant that combines conversational memory with ingested external sources to produce evidence-backed responses without overstating certainty or autonomy.

For stakeholder-critical outputs, trust must be measurable: responses should be attributable to explicit evidence references (for example `used_source_evidence_refs` plus `source_evidence_attribution` / `used_memory_refs` metadata) and fallback decisions should remain policy-explainable through directive traceability artifacts such as [docs/directives/traceability-matrix.md](docs/directives/traceability-matrix.md) and [docs/directives/decision-policy.md](docs/directives/decision-policy.md).

Non-goal: TestBot does not claim perfect truth, complete source coverage, or universally correct answers across all domains.

### How Vision is operationalized

Policy-facing, testable product principles that operationalize Vision claims are defined in [docs/directives/product-principles.md](docs/directives/product-principles.md).
- **Evidence-backed knowing responses**: source ingestion continuously normalizes external evidence into retrievable records, and knowing-mode answers include provenance so users can inspect what memory and source evidence informed the response.
- **Explicit uncertainty when evidence is weak or conflicting**: trust-tier metadata is preserved for ingested sources, and disagreement between memory and source evidence resolves to visible uncertainty/clarification behavior rather than unsupported claims.
- **Safe fallback and clarifier behavior**: deterministic fallback policy routes low-trust, unavailable, or conflicting evidence to safe fallback paths, including user-facing clarification prompts.

### Continuity commitments
- **`answer.commit` is mandatory continuity write-through**: each turn must persist confirmed user facts, obligations, repair state, and assistant-turn provenance so follow-up turns inherit durable state instead of re-deriving it.
- **Continuity evidence must stay traceable**: retrieval/context layers must treat `commit_receipt` artifacts (memory update receipts) as first-class continuity evidence so downstream behavior can point to committed anchors, not implicit guesswork.
- **Persistence must preserve user agency over time**: carrying forward explicit commitments lets users correct facts, close obligations, and steer repairs across turns with auditable state transitions.

TestBot operates in two explicit response intents:

- **Knowing mode**: provide an evidence-backed grounded answer with provenance for where the answer came from.
- **Unknowing mode**: do not fabricate; explicitly state uncertainty, keep confidence calibration visible to the user, and either ask for clarification or provide a safe fallback path.

### Start here by role
- **Operator**: setup and run guidance in [docs/quickstart.md](docs/quickstart.md).
- **Contributor / QA**: validation and readiness guidance in [docs/testing.md](docs/testing.md).
- **Designer / reviewer**: runtime contract overview in [docs/architecture/canonical-turn-pipeline.md](docs/architecture/canonical-turn-pipeline.md).

## Issue tracking (canonical, in-repo)

Project issue tracking is now standardized in-repo and remains the default workflow **until reviewed**.

- Canonical workflow: `docs/issues.md`
- Issue records: `docs/issues/`
- Red-tag escalation index: `docs/issues/RED_TAG.md`
- Program anchor: [`docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).

Use issue IDs (for example `ISSUE-0002`) in PR descriptions and non-trivial commit messages for any non-trivial change.

---
### Repository map (maintained)
Use this high-level map instead of a full tree snapshot:

- `src/testbot/` — runtime chatbot loop, memory recall, ranking, and mode orchestration.
- `features/` — behavior scenarios for answer contract, memory recall, and intent grounding.
- `tests/` — unit/integration-style Python test coverage.
- `docs/` — architecture, directives, testing policy, operations notes, and roadmap/status docs.
- `scripts/` — release gates and validation/automation helpers.
- `eval/` — evaluation fixtures and supporting artifacts.

For canonical project status and planned work, use `docs/roadmap/`.

### Product principles, roadmap, and status
- Product principles: [docs/directives/product-principles.md](docs/directives/product-principles.md)
- Roadmap: [docs/roadmap/next-4-sprints-grounded-knowing.md](docs/roadmap/next-4-sprints-grounded-knowing.md)
- Current status: [docs/roadmap/current-status-and-next-5-priorities.md](docs/roadmap/current-status-and-next-5-priorities.md)

## Grounding model
Authoritative runtime-contract and decision-policy references:

- [docs/architecture/canonical-turn-pipeline.md](docs/architecture/canonical-turn-pipeline.md)
- [docs/directives/traceability-matrix.md](docs/directives/traceability-matrix.md)
- [docs/directives/decision-policy.md](docs/directives/decision-policy.md)

Supporting verification-governance overview (non-authoritative):

- [docs/architecture/behavior-governance.md](docs/architecture/behavior-governance.md)
- [features/testbot/intent_grounding.feature](features/testbot/intent_grounding.feature)

## Current limitations
- External fact integrations are currently limited.
- Most grounding comes from conversation memory plus deterministic policy/routing behavior.
- For current validation expectations, see [docs/testing.md](docs/testing.md).
- For roadmap and delivery status, see [docs/roadmap/](docs/roadmap/).

## Setup and validation
Use role-based guides instead of duplicated install/readiness instructions:

- Setup/runtime: [docs/quickstart.md](docs/quickstart.md)
- Validation/readiness: [docs/testing.md](docs/testing.md)

## Contribute
Use [CONTRIBUTING.md](CONTRIBUTING.md) as the single gateway for contribution workflow, standards, and checks.
