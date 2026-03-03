# TestBot

A **Home Assistant Assist Satellite** chatbot with **local Ollama RAG memory** and **metacognitive reflection cards**.

This repo is a “small-but-serious” starting point for building a context-aware assistant that can:
- listen through a Home Assistant satellite channel (voice or text),
- store what was said as **structured memory cards**,
- generate **reflection cards** (thinking-about-thinking),
- retrieve relevant memories using **nomic-embed-text** embeddings,
- re-rank memories with a **time-aware probability distribution** around a target time inferred from phrases like “ago / in / from now”,
- answer strictly from retrieved memory + recent conversation window.

The immediate packaging scope is intentionally narrow: ship one externally valuable loop first (`sat_chatbot_memory_v2`) and defer extra governance/tooling complexity until real usage friction appears.

## v0 product contract

**Target user story (v0):** As a Home Assistant satellite user, I can ask a single memory-grounded question and get a relevant answer sourced from what I previously said in this bot loop.

**Success criteria (explicit):**
- **Relevance:** the answer is grounded in retrieved memory cards and does not invent facts outside memory context.
- **Latency:** typical end-to-end turn (input → retrieval → answer) should complete in about **5 seconds** on a healthy local HA + Ollama setup.
- **Citation behavior:** when memory is used, responses include the referenced `doc_id` and `ts`; when memory is insufficient, the assistant replies **"I don't know from memory."**

**Non-goals for v0 (deferred to v1+):**
- Multi-path command routing beyond start/stop of the core loop.
- User-facing memory editing controls (e.g., forget/delete flows).
- Advanced retrieval controls, policy/governance layers, and tuning dashboards.

---

## What we’re building

### The pipeline

1. **Observe**
   - User says something (via HA satellite)
   - System replies

2. **Encode memory**
   - Store an **utterance memory card** for each speaker (`user_utterance`, `assistant_utterance`)
   - Store a **reflection memory card** (`reflection`) linked to the utterance via `source_doc_id`

3. **Retrieve**
   - Rewrite the user utterance into a retrieval-friendly query
   - Pull top-k candidates from an in-memory vector store

4. **Re-rank**
   - Infer a *target time* from the utterance (“2 hours ago”, “last week”, etc.)
   - Apply a Gaussian time weight centered on that target time
   - Set σ (uncertainty) as a fraction of distance from now

5. **Answer**
   - Feed (a) recent chat window, (b) retrieved memory cards to Ollama
   - Enforce: **answer only from provided memory context**
   - Include `doc_id` and `ts` when referencing memories

---

## Repository layout

```
TestBot/
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ .gitignore
├─ src/
│  └─ testbot/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ memory_cards.py
│     ├─ time_parse.py
│     ├─ rerank.py
│     ├─ prompts.py
│     └─ sat_chatbot_memory_v2.py
└─ scripts/
   └─ run_sat.sh

````

Current packaging keeps `sat_chatbot_memory_v2` as the primary executable entrypoint.

---

## Requirements

- Python: 3.11+
- Home Assistant reachable via REST API
- Assist Satellite entity available and working
- Ollama running locally or reachable on your network

### Python deps

Core packages you’ll use:
- `homeassistant-api`
- `ha-ask` (Ask integration) https://github.com/neatbasis/Ask 
- `langchain-core`
- `langchain-ollama`
- `arrow`
- `python-dotenv` (optional but strongly recommended)

---

## Quickstart

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
````

### 2) Install dependencies

If you’re using `pip` directly:

```bash
pip install homeassistant-api ha-ask arrow python-dotenv langchain-core langchain-ollama
```

(We’ll pin versions later once we lock down compatibility.)

### 3) Start Ollama

Make sure Ollama is up:

```bash
ollama serve
```

Pull the models you’ll need:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 4) Configure environment

Copy the example env and fill it in:

```bash
cp .env.example .env
```

`.env.example` should contain:

```env
# Home Assistant
HA_API_URL=http://homeassistant.local:8123
HA_API_SECRET=YOUR_LONG_LIVED_TOKEN
HA_SATELLITE_ENTITY_ID=assist_satellite.your_satellite_entity

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
```

`OLLAMA_BASE_URL` is the canonical setting. `OLLAMA_HOST` is still accepted as a legacy fallback.

### 5) Run the bot

```bash
testbot
```

Direct module execution still works:

```bash
python src/testbot/sat_chatbot_memory_v2.py
```

Say “stop” to exit.

---

## Done definition (one-loop v0)

- [ ] One primary loop is intact: **input → retrieval (+ rerank) → answer**.
- [ ] No additional user command routes are required to complete the v0 story (besides stop/exit).
- [ ] Replies are memory-grounded and include `doc_id` + `ts` when citing retrieved context.
- [ ] If memory is insufficient, assistant uses: **"I don't know from memory."**
- [ ] End-to-end loop remains responsive for local use (target ~5s typical turn).

## Retrieval/rerank evaluation gate

Before expanding feature scope, run the offline memory-recall eval and review its metrics.

### Files

- `eval/cases.jsonl`: real/synthetic utterance cases with expected memory intent and target `doc_id`.
- `scripts/eval_recall.py`: offline replay runner for retrieval/rerank logic (no Home Assistant runtime dependency).

### Run

```bash
python scripts/eval_recall.py --cases eval/cases.jsonl --top-k 4
```

The script prints JSON metrics:

- `hit_at_k`
- `average_rank_expected_memory`
- `dont_know_from_memory_decisions`

Feature-scope rule: do not expand v0 behavior until this eval is run and these metrics are reviewed.

## Testing strategy

Keep the **default test suite deterministic and fast**. Anything that needs real Ollama/Home Assistant should be opt-in and excluded from quick local runs and default CI.

### Layer 1: Pure unit tests (no LangChain model calls)

These are the fastest and should form the core of day-to-day feedback:

1. `_parse_target_time`
2. `adaptive_sigma_fractional`
3. `time_weight`
4. rerank scoring behavior

Guidance:

- Use fixed `now` timestamps in fixtures.
- Assert exact/near-exact expected values and ordering.
- Keep these tests free of network, model, and Home Assistant dependencies.

### Layer 2: LangChain graph/component tests with fakes

Validate wiring and component interactions while still staying deterministic:

1. Query rewrite → retrieval → answer flow with fake/stubbed model outputs.
2. Vector search behavior using `DeterministicFakeEmbedding`.

Guidance:

- Stub rewrite/answer model calls with fixed outputs.
- Build `InMemoryVectorStore` with `DeterministicFakeEmbedding` (not `OllamaEmbeddings`).
- Keep fixtures small and explicit (about 3–8 memory cards) with known expected top-k ordering.

### Layer 3: Optional live integration smoke tests

Run separately when you want environment-level confidence:

- Real Ollama + Home Assistant environment.
- Mark these tests separately (for example with a `live` marker) and exclude by default.
- Use them as smoke checks, not as required gates for quick local iteration.

Recommended policy:

- Default local + CI run: Layer 1 + Layer 2 only.
- Opt-in command/profile for Layer 3 when local services are available.

Example pattern:

```python
from langchain_core.documents import Document
from langchain_core.embeddings.fake import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore


def test_retrieval_order_is_stable():
    embedding = DeterministicFakeEmbedding(size=32)
    store = InMemoryVectorStore(embedding=embedding)

    docs = [
        Document(page_content="type: user_utterance\ntext: I left keys in the garage", metadata={"doc_id": "m1"}),
        Document(page_content="type: user_utterance\ntext: Dentist appointment is Friday", metadata={"doc_id": "m2"}),
        Document(page_content="type: reflection\ntext: User often stores tools near garage shelf", metadata={"doc_id": "m3"}),
    ]
    store.add_documents(docs)

    results = store.similarity_search_with_score("where are my keys", k=2)

    top_ids = [doc.metadata["doc_id"] for doc, _score in results]
    assert top_ids == ["m1", "m3"]
```

---

## Memory cards

We store memory as text documents with stable field labels.

### Utterance card

```
type: user_utterance
ts: 2026-03-03T07:12:44.328511+00:00
speaker: user
channel: satellite
doc_id: ...
text: ...
```

### Reflection card

```
type: reflection
ts: ...
about: user
source_doc_id: <doc_id of utterance>
doc_id: ...
reflection:
claims: [...]
commitments: [...]
preferences: [...]
uncertainties: [...]
followups: [...]
confidence: 0.0..1.0
```

**Design rule:** reflections are hypotheses, always anchored to a source utterance.

---

## Time-aware retrieval

We parse human time cues like:

* “2 hours ago”
* “in 30 minutes”
* “from now”
* “last week”
* “next monday”

We compute:

* `target_time` from the utterance
* `σ = frac * |target_time - now|`
* a Gaussian time weight per memory card:

  * near target time → boosted
  * far away → suppressed

This gives you a crude but effective “temporal attention mechanism” over memory.

---

## Session logging (v0 loop)

`sat_chatbot_memory_v2` writes structured JSONL logs to:

```text
./logs/session.jsonl
```

Each line is one JSON object with a small schema shared across events:

* `ts`: log timestamp (UTC ISO8601)
* `event`: v0 loop event name
* event-specific keys

Current events:

* `user_utterance_ingest`
  * `channel`, `utterance`
* `query_rewrite_output`
  * `utterance`, `query`
* `retrieval_candidates`
  * `query`, `candidate_count`, `top_candidates` (`[{doc_id, score}, ...]`)
* `time_target_parse`
  * `utterance`, `now_ts`, `target_ts`, `sigma_seconds`
* `final_answer_mode`
  * `mode` (`memory-grounded` or `dont-know`), `query`, `retrieved_docs`

---

## Commands / Interaction patterns (planned)

This repo is early. A few useful “routes” you can add next:

* `recall: <query>` — force retrieval and show memory hits
* `reflect: <text>` — force reflection extraction
* `what did I say about <topic>` — topic recall
* `forget: <id>` — delete doc by id (works with InMemoryVectorStore if IDs are used)

---

## Safety & behavior constraints

**Non-negotiable v0 invariant (answer-generation contract):**

* Any factual answer must be grounded by at least one explicit memory citation containing both `doc_id` and `ts`.
* If retrieval/context confidence is insufficient, the assistant must return this exact string: `I don't know from memory.`
* Post-processing validates generated answers: when claims are present but required memory citation fields are missing, the output is forced to `I don't know from memory.`

* The assistant must be able to say:

  * **"I don't know from memory."**
* The assistant must not hallucinate facts that are not in memory context.
* Any reflection is explicitly labeled as inference (not ground truth).

---

## Roadmap

### v0 — working local demo (this repo)

* [x] HA satellite I/O loop
* [x] In-memory vector store
* [x] Ollama embeddings (`nomic-embed-text`)
* [x] Memory cards
* [x] Reflection cards
* [x] Time-aware re-ranking
* [ ] Basic commands (`recall:`, `forget:`)

### v1 — persistent memory and auditability

* [ ] ElasticsearchStore backend
* [ ] Deterministic IDs (hash-based)
* [ ] Append-only event log (JSONL)
* [ ] Replay runner

### v2 — stronger metacognition

* [ ] Pydantic schemas for reflections & extracted commitments
* [ ] Confidence tracking + decay
* [ ] Contradiction detection and reflection revision
* [ ] “Ask clarifying question” policy driven by expected value

---

## Troubleshooting

### “AttributeError: 'tuple' object has no attribute 'metadata'”

You used `similarity_search_with_score` but treated results like Documents.

Fix: it returns `(Document, score)` tuples; rerank/filter accordingly.

### HA API / token issues

Verify:

* `HA_API_URL` correct (and includes scheme)
* token is a valid long-lived token
* satellite entity id is correct and available

### Ollama connectivity

Verify:

* `OLLAMA_BASE_URL` points to your Ollama service
* model exists (`ollama list`)
* embeddings model exists (`nomic-embed-text`)

---

## License

Pick one. If this becomes a serious reusable base, Apache-2.0 is a good default.

---

## Notes

This repo is intentionally designed to be “small and hackable” while still pushing toward:

* structured memory
* temporal awareness
* reflection as first-class data
* no silent drift in meaning
