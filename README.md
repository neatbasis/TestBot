# TestBot

TestBot is a Home Assistant Assist Satellite chatbot that keeps local memory cards and answers from those memories. It combines Ollama embeddings, retrieval, and time-aware reranking so responses are memory-grounded in prior conversation context. The project is intentionally small so teams can iterate quickly on a reliable v0 loop.

## Quickstart

- Setup and run: [docs/quickstart.md](docs/quickstart.md)
- Architecture overview: [docs/architecture.md](docs/architecture.md)
- Testing approach: [docs/testing.md](docs/testing.md)
- Operations notes: [docs/ops.md](docs/ops.md)
- Documentation style guide: [docs/style-guide.md](docs/style-guide.md)
- Canonical directive terms: [docs/directives/terms.md](docs/directives/terms.md)


## Evaluation script notes

- `scripts/eval_recall.py` intentionally reuses `testbot.time_parse.parse_target_time` and `testbot.rerank` scoring primitives (including the shared similarity/time/type score function) so offline metrics track runtime behavior.
- The script keeps a thin dict-based adapter for candidate scoring because eval fixtures store plain JSON candidates rather than LangChain `Document` objects.
- This adapter is intentionally simplified: it mirrors the production score formula but does not instantiate full runtime document types.

## BDD-first policy

This repository is BDD-first for stakeholder-visible behavior. New capabilities should begin as plain-language `.feature` scenarios, then be implemented to satisfy those scenarios with deterministic checks. If behavior is not expressed in executable BDD scenarios (and supported by deterministic lower-level tests), it is not considered complete.

The core response contract is memory-grounded output with citation evidence; guardrail checks enforce fallback behavior when confidence is insufficient.

## Scope and roadmap contract

### v0 (current, in contract)

The v0 release contract is intentionally narrow:

- Memory-grounded responses from local memory cards.
- Citation evidence in factual answers.
- Deterministic fallback behavior when confidence is insufficient.
- BDD scenarios plus deterministic checks covering stakeholder-visible behavior.

### v1+ (planned, out of v0 contract)

The following are roadmap items and are **not** part of v0 acceptance:

- Commands / Interaction patterns (planned).
- Any expanded orchestration or UX features not explicitly listed in the v0 contract above.

Treat v1+ items as experimental/planned until promoted into the explicit contract.

## Done definition

A change is "done" for v0 when:

- It preserves the v0 contract above.
- It is covered by executable BDD scenarios and deterministic checks.
- It does not require v1+ planned features to pass acceptance.

**Acceptance rule:** Anything outside the v0 contract must not be required for acceptance.

## Start here by role

- **Stakeholder reviewer**
  - Read [docs/testing.md](docs/testing.md) to review behavior contract expectations and acceptance criteria.
  - Review [docs/architecture.md](docs/architecture.md) for pipeline expectations.
- **Feature author**
  - Start with [docs/testing.md](docs/testing.md) and write/update BDD scenarios first.
  - Use [docs/architecture.md](docs/architecture.md) to align with memory-card and rerank design.
  - Follow [docs/quickstart.md](docs/quickstart.md) for local setup and execution.
- **Runtime operator**
  - Use [docs/quickstart.md](docs/quickstart.md) for environment setup and startup.
  - Use [docs/ops.md](docs/ops.md) for logs, troubleshooting, and environment notes.

## Where to find what

| Topic | File | What it contains |
|---|---|---|
| Local setup and running the bot | `docs/quickstart.md` | Prerequisites, install steps, environment config, run commands |
| Core pipeline and retrieval design | `docs/architecture.md` | Observe→encode→retrieve→rerank→answer flow, memory cards, rerank overview |
| BDD and deterministic testing strategy | `docs/testing.md` | Behavior contract expectations, test layers, acceptance criteria/checklists |
| Canonical directive terminology | `docs/directives/terms.md` | Canonical terms, preferred usage, and avoid aliases |
| Logs and operational troubleshooting | `docs/ops.md` | Session log schema, common failures, environment notes |
| Documentation writing standards | `docs/style-guide.md` | Clarity/concision/consistency rules, required section questions, docs drift checks, review cadence |
