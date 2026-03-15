# Experiments

## 2026-03-15 seem_bot corner-case investigation

### Prompt sequence exercised
1. hi
2. what do you mean?
3. yes
4. no
5. Can you summarize what I asked?

### Iteration notes
- First iteration used direct phrase matching for corner cases.
- Second iteration replaced exact string matching with a reusable **dialogue-act feature extractor**:
  - token-level normalization (`_tokenize`)
  - short-utterance ambiguity features (confirmation/rejection/clarifier)
  - semantic-style summary request signals (`summarize/recap` + first-person + recall verbs)
- This follows higher-level TestBot pipeline ideas (resolve intent from enriched state, avoid brittle raw-text equality checks).

### Small changes tested in `examples/seem_bot.py`
- Added `_dialogue_act_features` for reusable intent/ambiguity detection.
- Updated `_intent_hint` to route by dialogue-act features instead of direct full-string equality checks.
- Kept deterministic guardrails in `answer_from_state`, but drive them via feature signals + state (`pending_focus`, recent passages).
- Kept summary handling and made it less brittle by using semantic indicators rather than one literal query phrase.

### Observed outcome from local scripted run
- Bare `yes` and `no` continue to get anchored follow-ups, now using feature-driven detection.
- Bare clarification prompts remain softer when no active referent exists.
- `Can you summarize what I asked?` returns prior user turns as bullet points (excluding the summary request itself).
