# TestBot

A **Home Assistant Assist Satellite** chatbot with **local Ollama RAG memory** and **metacognitive reflection cards**.

This repo is a “small-but-serious” starting point for building a context-aware assistant that can:
- listen through a Home Assistant satellite channel (voice or text),
- store what was said as **structured memory cards**,
- generate **reflection cards** (thinking-about-thinking),
- retrieve relevant memories using **nomic-embed-text** embeddings,
- re-rank memories with a **time-aware probability distribution** around a target time inferred from phrases like “ago / in / from now”,
- answer strictly from retrieved memory + recent conversation window.

The goal is not “a chat demo”, but an **evolvable substrate** you can later harden into:
- an Elasticsearch-backed long-term store,
- better schema’d memory (Pydantic contracts),
- quality gates (invariants, trace logs),
- and richer agent behaviors.

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

## Repository layout (proposed)

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

You can keep it as a single script initially, then extract modules as it stabilizes.

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
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
```

### 5) Run the bot

```bash
python src/testbot/sat_chatbot_memory_v2.py
```

Say “stop” to exit.

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

## Commands / Interaction patterns (planned)

This repo is early. A few useful “routes” you can add next:

* `recall: <query>` — force retrieval and show memory hits
* `reflect: <text>` — force reflection extraction
* `what did I say about <topic>` — topic recall
* `forget: <id>` — delete doc by id (works with InMemoryVectorStore if IDs are used)

---

## Safety & behavior constraints

* The assistant must be able to say:

  * **“I don’t know from memory.”**
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

* `OLLAMA_HOST` points to your Ollama service
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
