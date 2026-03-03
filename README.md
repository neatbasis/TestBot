# TestBot

TestBot is a Home Assistant Assist Satellite chatbot that keeps local memory cards and answers from those memories. It combines Ollama embeddings, retrieval, and time-aware reranking so responses are grounded in prior conversation context. The project is intentionally small so teams can iterate quickly on a reliable v0 loop.

## Quickstart

- Setup and run: [docs/quickstart.md](docs/quickstart.md)
- Architecture overview: [docs/architecture.md](docs/architecture.md)
- Testing approach: [docs/testing.md](docs/testing.md)
- Operations notes: [docs/ops.md](docs/ops.md)
- Documentation style guide: [docs/style-guide.md](docs/style-guide.md)

## BDD-first policy

This repository is BDD-first for stakeholder-visible behavior. New capabilities should begin as plain-language `.feature` scenarios, then be implemented to satisfy those scenarios with deterministic checks. If behavior is not expressed in executable BDD scenarios (and supported by deterministic lower-level tests), it is not considered complete.

## Start here by role

- **Stakeholder reviewer**
  - Read [docs/testing.md](docs/testing.md) to review behavior contracts and acceptance criteria.
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
| BDD and deterministic testing strategy | `docs/testing.md` | Behavior contracts, test layers, acceptance criteria/checklists |
| Logs and operational troubleshooting | `docs/ops.md` | Session log schema, common failures, environment notes |
| Documentation writing standards | `docs/style-guide.md` | Clarity/concision/consistency rules, required section questions, docs drift checks, review cadence |
