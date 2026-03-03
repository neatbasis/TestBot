# BDD + Gherkin Guide for TestBot

This guide defines how TestBot uses **Gherkin** to connect:

- **Human-facing intent** (why stakeholders care), and
- **Software-facing acceptance criteria** (what automated tests must verify).

Primary syntax reference: Behave Gherkin docs.

- https://behave.readthedocs.io/en/stable/gherkin/

---

## 1) Why Gherkin matters by stakeholder group

### Business / Domain experts

- Scenarios describe behavior in domain language, not implementation internals.
- Feature narrative (`In order to / As a / I want`) makes business value explicit.
- Scenario titles describe outcomes stakeholders can validate.

### Product owners

- Acceptance is example-driven and auditable.
- Coverage gaps are visible by reading feature files.
- Tags can map scenarios to business rules and priority.

### Engineering / QA

- Scenarios are executable via Behave step definitions.
- Contracts (citations, fallback text, ranking outcomes) are tested deterministically.
- Shared phrasing enables reusable step definitions and less duplication.

---

## 2) Gherkin structure: human narrative + measurable precision

A complete scenario has three visible layers:

- **Given**: business context and system preconditions.
- **When**: single trigger action.
- **Then**: observable, verifiable outcomes.

In TestBot, we also require two hidden dimensions to keep behavior governance strong:

1. **Role & concern narrative** at Feature level (`In order to / As a / I want`).
2. **Rule traceability metadata** via tags (example: `@Rule:CitationContract`, `@Priority:High`).

---

## 3) Scenario format (Given/When/Then)

Use this canonical shape:

```gherkin
Scenario: <human-meaningful observable behavior>
  Given <deterministic business context>
  When <single user or system action>
  Then <observable outcome>
```

Use `And`/`But` only to keep one behavior readable, not to bundle multiple behaviors.

---

## 4) Naming conventions

### Feature file names

- Use domain + contract/outcome naming.
- Examples:
  - `memory_citation_contract.feature`
  - `fallback_contract.feature`

### Feature title + narrative block

Every feature should include the role-taking narrative:

```gherkin
Feature: <capability in stakeholder terms>
  In order to <business outcome>
  As a <role>
  I want <capability>
```

### Scenario names

- One scenario = one observable business behavior (clear grain).
- Prefer outcome-centric names over technical names.
- Examples:
  - `Cited memory answer when context is sufficient`
  - `Exact fallback when context is insufficient`

### Step wording

- Stakeholder-readable language first; technical detail second.
- Prefer: `Given the clock is fixed at "2024-10-01T09:00:00Z" for deterministic ranking`
- Avoid: `Given rerank.py returns score > 0.8`

---

## 5) Behavioral modeling rule (star-schema analogy)

Treat Gherkin as a **behavioral dimensional model**:

- **Scenario** ≈ behavioral fact.
- **Given context** ≈ dimensions.
- **When** ≈ event trigger.
- **Then assertions** ≈ measurable outcomes.
- **Tags** ≈ metadata keys for governance.

### Grain rule (mandatory)

Define and preserve grain as:

- **One scenario per observable business behavior.**

If a scenario asserts multiple independent behaviors, split it.

---

## 6) Step-definition rules (mandatory)

1. **One behavior per step**
   - A single step should express one business behavior.
   - Do not combine retrieval setup and final answer contract in one step.

2. **Reusable retrieval/rerank/citation steps**
   - Reuse common steps for:
     - retrieval assertions (relevant match / no relevant match)
     - rerank ordering assertions under fixed-time context
     - citation assertions (`doc_id`, `ts`)
   - Keep phrase stability so multiple features bind to the same step definitions.

3. **Deterministic fixtures required**
   - Freeze time for temporal interpretation/rerank scenarios.
   - Use fixed candidate sets and stable memory fixtures.
   - No network/model nondeterminism in default BDD suite.

4. **Then steps must be measurable**
   - Assert observable outputs only (string, fields, ordering, state).
   - Avoid subjective assertions that cannot be machine-verified.

---

## 7) Traceability tags and conventions

Use tags to map scenarios to business rules, roles, and priority.

Recommended pattern:

```gherkin
@Rule:CitationContract @Role:Resident @Priority:High @fast
Scenario: Cited memory answer when context is sufficient
```

Tag guidance:

- `@Rule:<ID-or-name>`: links scenario to policy/contract.
- `@Role:<persona>`: expresses primary stakeholder lens.
- `@Priority:<High|Medium|Low>`: supports triage.
- `@fast`/`@slow`: enables fast local loops.

---

## 8) Reference scenarios (canonical)


### Descriptor requirement for every feature example

Every feature example in this document must include the following descriptor shape exactly:

```gherkin
Feature: <Clear capability statement>
  In order to <business outcome>
  As a <role/title>
  I want <capability/feature>
```

```gherkin
@Rule:CitationContract @Role:Resident @Priority:High @fast
# Descriptor (mandatory)
Feature: Memory-grounded answer contract
  In order to trust answers with source context
  As a resident
  I want answers to include citations when memory is sufficient

  # Grain: one scenario per answer contract behavior
  Scenario: Cited memory answer when context is sufficient
    Given the clock is fixed at "2024-10-01T09:00:00Z"
    And the memory store contains a relevant fact for "When is garbage pickup?"
    When the user asks "When is garbage pickup?"
    Then the assistant answer is grounded in memory
    And the answer includes citation fields "doc_id" and "ts"
```

```gherkin
@Rule:FallbackContract @Role:Resident @Priority:High @fast
# Descriptor (mandatory)
Feature: Exact fallback contract when context is missing
  In order to avoid fabricated answers
  As a resident
  I want the assistant to return an exact fallback when memory is insufficient

  # Grain: one scenario per fallback contract behavior
  Scenario: Exact fallback when context is insufficient
    Given the clock is fixed at "2024-10-01T09:00:00Z"
    And the memory store has no relevant fact for "What is the HOA gate code?"
    When the user asks "What is the HOA gate code?"
    Then the assistant responds exactly "I don't know from memory."
```

---

## 9) Local run commands and expected outputs

Run full BDD suite:

```bash
behave
```

Expected output shape:

- All selected scenarios pass.
- No undefined steps.
- Exit code is `0`.

Fast local loops with scenario-name filters:

```bash
behave -n "Cited memory answer when context is sufficient"
behave -n "Exact fallback when context is insufficient"
```

Fast local loops with tags:

```bash
behave --tags=@fast
behave --tags='not @slow'
behave --tags='@Rule:CitationContract'
```

Filtered-run expectation:

- Only matching scenarios execute.
- Non-selected scenarios are skipped.
- Exit code is `0` when selected scenarios pass.

---

## 10) Step definition binding pattern (example)

Example showing human-readable phrasing mapped to executable code:

```python
from behave import given

@given('{role} has initiated a dispute for {transaction_type}')
def step_impl(context, role, transaction_type):
    context.role = role
    context.transaction_type = transaction_type
```

The key rule is to keep the Gherkin phrase stakeholder-readable while preserving deterministic code-level binding.

---

## 11) Definition of Done for docs + BDD (PR checklist)

- [ ] Feature includes `In order to / As a / I want` narrative when applicable.
- [ ] Scenario grain is explicit: one scenario per observable behavior.
- [ ] Scenario/step wording is stakeholder-readable.
- [ ] `Then` assertions are objectively measurable.
- [ ] Retrieval/rerank/citation checks use reusable step definitions.
- [ ] Deterministic fixtures are used (fixed time + fixed candidate set).
- [ ] Rule/role/priority tags are applied where relevant.
- [ ] `behave` passes with no undefined steps.
- [ ] Exact fallback contract is preserved: `I don't know from memory.`
