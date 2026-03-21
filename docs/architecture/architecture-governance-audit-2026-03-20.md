# Architecture Governance Audit — 2026-03-20

## Scope and method

This audit reviews:

- Open PRs: `#597`, `#595`, `#594`, `#590`, `#589`, `#585`.
- Current `src/testbot/` package structure, root-level authority, dependency direction reality, and test-enforcement posture.

This is **not** a general code review. It is a structural-honesty audit for a mixed-state pivot where package naming can overstate migration progress.

Evidence used:

1. Open PR metadata and changed-file deltas from GitHub pull-request APIs.
2. Current repository code structure and imports under `src/testbot/`.
3. Existing architecture boundary tests and architecture docs.

---

## 1) Executive summary

The pivot is partially real but structurally fragile, with the strongest evidence concentrated in directory-conformity and root-authority drift.

Positive movement exists (new packages, orchestration seams, compatibility metadata), but major runtime authority is still concentrated in root-level legacy modules—especially `sat_chatbot_memory_v2.py`. Several new package modules are currently façade/re-export layers over root modules rather than independent behavioral owners.

### Early signs of pivot failure

1. **Decorative/misleading package ownership**
   - `domain/turn_pipeline.py` and `logic/turn_pipeline.py` primarily aggregate root modules rather than owning the behavior they name.
2. **Entrypoint dependency inversion is incomplete**
   - `entrypoints/sat_cli.py` still imports core runtime behavior from `sat_chatbot_memory_v2.py`.
3. **Compatibility seams are broad in the monolith**
   - compatibility exports and deprecated aliases remain in canonical runtime module surface.
4. **Documented dependency model exceeds enforcement reality**
   - import-boundary checks are helpful but narrower than the full target correspondence rules.
5. **Policy layer remains structurally unresolved**
   - target map names `policies/`, but policy authority remains in root modules.
6. **All currently reviewed open PRs are not merge-safe for pivot governance**
   - PRs `#597`, `#595`, `#594`, `#590`, `#589`, and `#585` all preserve or harden transitional drift enough to classify as `do-not-merge` for structural governance purposes.

### Stabilizing signs

1. Compatibility controls now include explicit metadata/removal criteria for key aliases/re-exports.
2. Boundary tests exist and currently pass for their declared scope.
3. Pivot docs explicitly mark unresolved enforcement and remaining migration obligations.

---

## 2) PR review table (supporting evidence; all current verdicts are do-not-merge)

| PR | Verdict | Authority effect on `sat_chatbot_memory_v2.py` | Ownership movement | Duplicate-source-of-truth risk | Compatibility placement | Test-evidence classification | Quality-characteristic impact (ISO/IEC 25010) | Foul-code signs | Minimal remediation before merge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| #597 | `do-not-merge` | Increases (monolith logic edits continue) | Mixed: some service fixes, monolith still patched directly | Preserved | Partial core-path leakage | Both target + transitional | Modularity mixed; Modifiability improved for bug fix but still coupled; Testability improved behavior checks | Monolith patch accretion across fallback/decision paths | Add explicit guard that monolith changes are compatibility-only unless issue-linked ownership migration is included |
| #595 | `do-not-merge` | Slight increase in compatibility metadata footprint | No major ownership transfer; compatibility contract extension | Slightly increased, governed | Boundary-local | Transitional only | Modularity neutral/slightly negative; Modifiability positive for safe migration; Testability positive (compat tests) | Adds compatibility surface instead of reducing it | Do not merge; carry only as issue-linked reference for compatibility risk inventory |
| #594 | `do-not-merge` | Same direction as #595 with weaker governance evidence | No meaningful ownership transfer | Redundant with #595 | Boundary-local but weaker than #595 | Transitional only | Redundant compatibility expansion with no structural convergence evidence | Duplicate PR scope for same compatibility export | Do not merge; close without replacement in pivot-hardening phase |
| #590 | `do-not-merge` | None (artifact/docs only) | None | None direct | N/A | Neither clearly for target boundaries | Modularity neutral; Modifiability helps triage; Testability evidence-only | Large raw artifact payload risks governance noise/staleness | Do not merge into mainline; keep as external investigation notes until converted to concise governed evidence |
| #589 | `do-not-merge` | Preserves root authority indirectly (contracts moved, but not into `domain/`) | Partial move with placement mismatch | Reduced type duplication, but new ownership ambiguity | N/A | Both | Modularity partial gain; Modifiability improved type reuse; Testability modest gain | “Domain-owned” contracts created as root module (`domain_contracts.py`) | Do not merge until contracts are placed in canonical package ownership and guarded by enforced correspondence rules |
| #585 | `do-not-merge` | Preserve/slight increase via delegators + monolith-provided dependencies | Seams added, but canonical ownership still split | Preserved | Mixed: boundary-local plus core-path compatibility leakage | Both | Modularity partial gain; Modifiability improved seamability; Testability good equivalence checks but not completion evidence | New entrypoint module still rooted in legacy imports | Do not merge until compatibility delegators are boundary-local only and monolith authority measurably shrinks |

---

## 3) Directory conformity table (primary findings)

| Directory | Intended purpose | Actual role today | Conformity | Missing authority / should migrate here | Dependency rule status (42010 correspondence) | Risk classification | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `domain/` | Pure state/contracts; no legacy runtime authority | DTO wrappers + compatibility import façade | Low | `pipeline_state` domain core; intent/decision contracts | `violated` / effectively `unenforced` | Misleading / transitional | Move shared contracts into `domain/`; ban domain imports from root behavior modules |
| `logic/` | Pure transformations over domain | Mix of real logic (`alignment`) and re-export aggregation (`turn_pipeline`) | Partial | Stabilization/retrieval pure slices | `unenforced` | Transitional | Replace façade exports with owned logic implementations |
| `policies/` | Policy ownership layer | Missing; policy authority remains root-level | Non-conformant | `policy_decision.py`, `answer_policy.py`, policy portions of fallback/decision modules | `unenforced` | Decorative-by-absence | Create package and move policy owners with explicit API |
| `application/` | Orchestration/services only | Real orchestration seam exists but root-coupled wrappers remain | Medium | Canonical orchestration currently split with monolith wrappers | `unenforced` | Transitional | Continue extraction; remove compatibility exports from service wrapper paths |
| `ports/` | Protocol interfaces + typed DTO boundaries | Real port module exists; some compatibility-typed signatures remain loose | Medium | Strongly typed memory-store/runtime contracts | `unenforced` (strict typing direction) | Transitional/authoritative mix | Tighten protocol typing and enforce contract tests |
| `adapters/` | Concrete infra implementations behind ports | Mostly thin factory façade | Low | `vector_store.py`, `source_connectors.py` concrete adapters | `unenforced` | Decorative | Relocate concrete adapters under structured subpackages |
| `entrypoints/` | Boot/wiring/startup composition only | Still imports substantial monolith runtime surface | Partial | Runtime functions currently in `sat_chatbot_memory_v2.py` | `violated-ish` / `unenforced` | Transitional / misleading | Invert dependency so monolith depends on entrypoint compatibility, not vice versa |
| `observability/` | Telemetry/logging/tracing only | Mostly telemetry utility with legacy utility coupling | Mostly conformant | Time/clock boundary normalization | `unenforced` | Transitional | Route timestamps through domain clock boundary |
| `pipeline/` | Stage orchestration/stateflow or explicit metrics scope | Mostly metrics; orchestration authority remains elsewhere | Ambiguous | Explicit stage orchestration authority if intended | `unenforced` | Decorative/transitional | Finish file-level census and declare explicit ownership scope |

---

## 4) Root-level authority table (primary findings)

| Module | Current real role | Still authoritative? | Canonical target directory | Root retention justified? | Justification category | Migration blocker | Test risk if moved now | Recommended next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `sat_chatbot_memory_v2.py` | Runtime mega-orchestrator + compatibility export hub | Yes | `entrypoints/` + `application/services/` + `policies/` | Partly (compatibility), but oversized authority | Justified transitional hold (overextended) | Broad caller/test surface | High | Split first; keep only boundary-local compatibility shell with expiry |
| `pipeline_state.py` | Canonical cross-stage state authority | Yes | `domain/` | Transitional only | Unjustified authority retention (long-term) | Legacy coupling + broad imports | Medium-high | Migrate now incrementally (DTO-first) |
| `stabilization.py` | Pre-route stabilization + storage coupling | Yes | `logic/` (+ adapters via ports) | Transitional only | Justified transitional hold | Mixed pure/infra responsibilities | Medium | Split first into pure planner + persistence adapter path |
| `evidence_retrieval.py` | Retrieval policy + provider-shape mapping | Yes | `logic/` + `ports/` + `adapters/` | Transitional only | Justified transitional hold | DTO/port extraction incomplete | Medium-high | Split first with port contracts and DTO mapping boundary |
| `answer_commit.py` | Commit orchestration + persistence semantics | Yes | `application/` (+ ports/adapters edge) | Transitional only | Justified transitional hold | Compatibility wrappers + call-graph depth | Medium | Freeze-and-wrap, then migrate core ownership |
| `policy_decision.py` | Decision classes/objects + retrieval-policy decisions | Yes | `policies/` (or split: domain types + policy logic) | No (long-term) | Unjustified authority retention | Missing policy package ownership | Medium | Migrate now and enforce imports |
| `answer_policy.py` | Fallback/answer-mode policy decisioning | Yes | `policies/` | No (long-term) | Unjustified authority retention | Policy-layer package absent | Medium | Migrate now with boundary tests |
| `vector_store.py` | Concrete memory/vector adapter | Yes | `adapters/memory/` | Temporary only | Compatibility-only / transitional | Callers import root path | Medium | Keep temporarily with explicit expiry and relocation shim |
| `source_connectors.py` | Connector adapter implementations | Yes | `adapters/` | Temporary only | Compatibility-only / transitional | Dynamic loading contract edges | Medium | Split first into adapter package + contract tests |
| `canonical_turn_orchestrator.py` | Canonical stage-order orchestration engine | Yes | `application/orchestrators/` (or explicitly retained root canonical) | Unclear | Unclear | Existing allowlists and import usage | Medium | Investigate and explicitly declare final ownership policy |

---

## 5) Final synthesis

### Earliest signs of pivot collapse

1. New package modules acting as wrappers over unchanged root authority.
2. Entrypoints still depending on monolith runtime symbols.
3. Compatibility pathways expanding without equivalent shrinkage of core legacy ownership.
4. “All green” checks that validate scoped constraints but not full dependency correspondence.

### Where architecture is real vs still fiction

- **Real:** service-layer seam exists; selected compatibility controls are explicit; targeted boundary checks are active.
- **Still fiction/partial:** complete dependency-direction contract is not yet enforced; ownership remains root-heavy; `policies/` target layer is not materially established.

### Root authorities that must shrink next

1. `sat_chatbot_memory_v2.py`
2. policy ownership modules (`policy_decision.py`, `answer_policy.py`)
3. retrieval/stabilization/commit root modules (`evidence_retrieval.py`, `stabilization.py`, `answer_commit.py`)

### Directory status snapshot

- **Mostly authoritative (partial):** `application/`, `ports/`
- **Transitional/misleading:** `domain/`, `logic/`, `entrypoints/`
- **Decorative/underpowered:** `adapters/`, `pipeline/`
- **Missing expected authority:** `policies/`

### Highest-risk mistake to avoid

Allowing new behavior/policy fixes to continue landing in `sat_chatbot_memory_v2.py` without strict “compatibility-only boundary” governance. That hardens duplicate authority and turns transitional seams permanent.

---

## Evidence anchors in current repo

- Target package map and dependency direction policy: `docs/pivot.md`.
- Remaining-work and enforcement-open signals (`ISSUE-0013-E` not complete): `docs/pivot.md` checklist.
- Boundary rules currently enforced by tests: `docs/architecture-boundaries.md` + `tests/architecture/test_import_boundaries.py`.
- Current façade/re-export patterns and compatibility metadata:
  - `src/testbot/domain/turn_pipeline.py`
  - `src/testbot/logic/turn_pipeline.py`
  - `src/testbot/sat_chatbot_memory_v2.py`
  - `src/testbot/entrypoints/sat_cli.py`
