# Rule Governance Matrix for Feature Verification

This matrix governs **test/spec traceability and overlap resolution only**. Runtime behavior authority remains defined by the canonical turn pipeline architecture and linked issue/program records.

- Source-of-truth hierarchy for behavior definition: architecture + canonical issue/program docs first, executable feature files second.
- Feature files are the executable verification surface for those canonical rules, not replacement ownership authorities.

## Canonical governance anchors

- Architecture contract: [`docs/architecture.md`](../architecture.md) and [`docs/architecture/canonical-turn-pipeline.md`](../architecture/canonical-turn-pipeline.md).
- Canonical program anchor for pipeline bug elimination and sequencing: [`docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).
- Cross-stage traceability baseline: [`docs/directives/traceability-matrix.md`](../directives/traceability-matrix.md).

## Domain matrix (verification governance)

| Rule / domain name | Governing architecture or issue/program reference | Primary feature verification surface | Secondary feature surfaces (overlap allowed) | Precedence for overlapping/conflicting test expectations |
| --- | --- | --- | --- | --- |
| Ambiguity handling (`@Rule:AmbiguityHandling`) | `intent.resolve` + `policy.decide` governance in `docs/architecture/canonical-turn-pipeline.md`; ISSUE-0013 decisioning checkpoint | `features/intent_grounding.feature` | `features/memory_recall.feature`, `features/answer_contract.feature` | If ambiguity assertions diverge, align to canonical decisioning definitions in architecture + ISSUE-0013 first, then treat `intent_grounding.feature` as tie-break verification surface for expected behavior language. |
| Temporal routing / time-aware rerank (`@Rule:TemporalRouting`) | `retrieve.evidence` + rerank semantics in `docs/architecture/canonical-turn-pipeline.md`; ISSUE-0013 decisioning checkpoint | `features/time_awareness.feature` | `features/memory_recall.feature`, `features/intent_grounding.feature` | If temporal assertions diverge, architecture/ISSUE-0013 constraints decide expected semantics; `time_awareness.feature` is the primary executable contract for deterministic temporal routing wording and outcomes. |
| Source-backed answer attribution (`@Rule:SourceBackedAnswer`) | `answer.assemble` + `answer.validate` provenance/citation contract in `docs/architecture/canonical-turn-pipeline.md`; ISSUE-0013 commit/audit checkpoint | `features/source_ingestion.feature` | `features/intent_grounding.feature`, `features/answer_contract.feature` | If source-attribution checks conflict, resolve against architecture provenance/validation rules first; use `source_ingestion.feature` as the canonical executable attribution surface for source evidence fields and fallback boundaries. |
| Fallback class semantics (`@Rule:FallbackSemantics`) | `policy.decide` fallback classing and `answer.validate` safety contract in `docs/architecture/canonical-turn-pipeline.md`; ISSUE-0013 decisioning + commit/audit checkpoints | `features/answer_contract.feature` | `features/memory_recall.feature`, `features/intent_grounding.feature`, `features/source_ingestion.feature` | If fallback class expectations overlap or conflict, architecture + ISSUE-0013 policy/validation checkpoints are authoritative; `answer_contract.feature` is the primary executable arbitration surface for fallback action/result semantics. |

## Overlap-resolution protocol (test/spec governance)

When two or more feature files appear to assert different outcomes for the same rule domain:

1. Confirm the intended canonical behavior in architecture + canonical issue/program docs.
2. Keep or update the **primary** feature surface for the domain so it expresses that canonical behavior unambiguously.
3. Update secondary feature assertions to remain consistent with the primary surface and canonical docs.
4. Preserve `@Rule:*` tags on all overlapping scenarios so cross-feature traceability remains explicit.

This protocol does not create feature-vs-feature runtime ownership. It defines how verification artifacts stay coherent with canonical architecture and program governance.
