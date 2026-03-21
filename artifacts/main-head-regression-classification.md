# Main-head regression classification

| Cluster | Classification | Rationale |
|---|---|---|
| A. Missing `CanonicalTurnOrchestrator` compatibility export | **Compatibility regression** | Backward-compatible module contract expected by tests is missing. |
| B. Seeded-store self-retrieval + fallback/GK drift | **Product regression** | Runtime behavior chooses wrong evidence/routing and violates stated answer contracts. |
| C. answer.commit confirmed fact merge | **Product regression** | Commit continuity behavior changed incorrectly relative to contract. |
| D. commit receipt continuity anchor additions | **Unclear** | Could be intended schema evolution or unintended drift; tests and behavior are out of sync. |
| E. DTO `None` vs `{}` adapter roundtrip | **Compatibility regression** | Legacy adapter identity expectations are broken by normalization behavior. |
| F. live smoke degraded-mode matrix failures | **Unclear (likely downstream of product regression)** | Failures are contract-level; dominant signal points to dependency on Cluster B, but classification remains conservative until isolated reruns after B is fixed. |

## Explicit investigation checklist mapping
- Wrong `fallback_action` / `answer_mode` / GK semantics: **Cluster B**.
- `answer.commit.post` invariant failures: **Cluster B** downstream manifestation.
- Wrong memory provenance / wrong cited doc_ids: **Cluster B** (self-retrieval contamination).
- Commit receipt / continuity drift: **Clusters C + D**.
- Missing `CanonicalTurnOrchestrator` compatibility export: **Cluster A**.
- Time-query regressing to generic uncertainty: **Cluster B**.
