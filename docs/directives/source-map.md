# Directive Source Map

This document maps the major behavior and process directives in TestBot to their sources, how they are enforced, and whether they are hard constraints (`enforced`) or guidance (`advisory`).

Program linkage: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; contributors should triage canonical pipeline defects and follow-on work against ISSUE-0013 first, with ISSUE-0012 treated as linked delivery planning context in [`ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`](../issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md).

## 1) Runtime-enforced directives (`src/testbot/sat_chatbot_memory_v2.py` guardrails, logging, fallback)

| Directive | Source location | Enforcement mechanism | Confidence level |
|---|---|---|---|
| Answer must be memory-grounded and use only provided context + recent chat. | `ANSWER_PROMPT` system instructions in `src/testbot/sat_chatbot_memory_v2.py`. | Prompt-level runtime instruction passed to the model on every response generation. | **Advisory** (LLM-followed instruction, not a static type/runtime assert by itself). |
| Memory-insufficient turns use progressive fallback (bridging clarifier, assist alternatives, or explicit uncertainty) instead of direct memory fallback. | `ANSWER_PROMPT` guidance + `decide_fallback_action(...)` + deterministic branches in `stage_answer(...)` (`build_partial_memory_clarifier`, `ASSIST_ALTERNATIVES_ANSWER`, `NON_KNOWLEDGE_UNCERTAINTY_ANSWER`). | Deterministic answer-stage routing applies policy-selected progressive fallback behavior when confidence/contract checks fail. | **Enforced**. |
| Factual answers must include citation fields (`doc_id` and `ts`). | `validate_answer_contract()`, `response_contains_claims()`, `has_required_memory_citation()`. | Regex-based post-generation contract check; non-compliant outputs are replaced with fallback. | **Enforced**. |
| Session observability for ingest/retrieval/answer decisions. | `append_session_log()` and call sites (`user_utterance_ingest`, `query_rewrite_output`, `retrieval_candidates`, `time_target_parse`, `final_answer_mode`). | Deterministic JSONL logging at key pipeline stages during runtime loop. | **Enforced** (when loop runs and log path writable). |
| Temporal retrieval behavior should track parsed target time and adaptive sigma. | `parse_target_time(...)`, `adaptive_sigma_fractional(...)`, and rerank call wiring. | Runtime rerank pipeline computes target/sigma and uses them in ranking; logged for auditability. | **Enforced**. |

## 2) Documentation directives (`README.md` v0 contract, testing policy, BDD requirement)

| Directive | Source location | Enforcement mechanism | Confidence level |
|---|---|---|---|
| v0 scope: small, reliable memory loop for rapid iteration. | Project description text in `README.md` (`reliable v0 loop`, intentionally small). | Human-facing scope contract for contributors/reviewers. | **Advisory**. |
| BDD-first policy for stakeholder-visible behavior. | `README.md` section `## BDD-first policy`. | Process expectation: features begin as `.feature` scenarios before implementation. | **Advisory** (policy-level; enforced socially/review-wise unless CI gates added). |
| Testing policy references deterministic checks + behavior contracts. | `README.md` links to `docs/testing.md` and role guidance. | Documentation-driven workflow: contributors are directed to required testing approach. | **Advisory**. |

## 3) Tooling directives (`pyproject.toml` dependencies and dev testing stack)

| Directive | Source location | Enforcement mechanism | Confidence level |
|---|---|---|---|
| Runtime dependency baseline for the chatbot stack. | `[project].dependencies` in `pyproject.toml`. | Packaging/install resolution enforces required libs for runtime execution. | **Enforced** (at install/runtime import boundaries). |
| Dev testing/lint/type-check stack (`behave`, `pytest`, `ruff`, `mypy`). | `[project.optional-dependencies].dev` in `pyproject.toml`. | Optional dev extra declares expected local/CI tooling. | **Advisory** (unless CI/scripts explicitly require all tools). |
| Entry point contract for launching the bot (`testbot` script). | `[project.scripts]` in `pyproject.toml`. | Installer creates CLI entry point bound to `testbot.sat_chatbot_memory_v2:main`. | **Enforced** (packaging-level). |

## 4) Eval directives (`scripts/eval_recall.py`, `eval/cases.jsonl`)

| Directive | Source location | Enforcement mechanism | Confidence level |
|---|---|---|---|
| Offline evaluation computes retrieval/ranking metrics (`hit_at_k`, rank, IDK decisions). | `evaluate(...)` in `scripts/eval_recall.py`. | Deterministic scoring pipeline over fixed candidate sets. | **Enforced** (within eval script execution). |
| Temporal interpretation heuristic for utterances (`last night`, `earlier this week`, duration phrases). | `parse_target_time(...)` in `scripts/eval_recall.py`. | Rule-based parsing used directly by eval ranking flow. | **Enforced** (inside eval). |
| IDK decision thresholding for weak top score. | `--idk-threshold` arg and `top_score < idk_threshold` check in `scripts/eval_recall.py`. | Deterministic decision counter for “don’t know from memory” behavior in eval metrics. | **Enforced** (inside eval). |
| Canonical evaluation fixtures define expected memory target behavior. | `eval/cases.jsonl` records with `expected_intent`, `expected_doc_id`, and candidate sets. | Data contract consumed by eval script to benchmark ranking/IDK outcomes. | **Enforced** for eval runs; **advisory** for production runtime unless mirrored by tests/CI. |
