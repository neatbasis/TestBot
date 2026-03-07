@Rule:CitationContract @Role:Resident @Priority:High @fast
Feature: Memory recall behavior
  In order to trust responses grounded in memory
  As a resident
  I want cited answers when memory is sufficient and progressive fallback when it is not

  Scenario: cited memory-grounded answer path
    Given a deterministic in-memory recall harness
    And eval cases are loaded from "eval/cases.jsonl"
    When the user asks about eval case "sleep-followup"
    Then the assistant returns a memory-grounded answer
    And the answer includes citation fields "doc_id" and "ts"
    And the response includes memory provenance transparency fields
    And the response includes a grounding basis statement

  Scenario: progressive assist fallback path
    Given a deterministic in-memory recall harness
    And eval cases are loaded from "eval/cases.jsonl"
    When the user asks about eval case "no-memory-match"
    Then the assistant returns an assistive fallback response

  Scenario: equivalent candidates remain ambiguous after tie-break
    Given a deterministic in-memory recall harness
    When equivalent top candidates remain after tie-break
    Then the assistant returns a bridging clarification response

  Scenario: pronoun temporal follow-up resolves anchor before routing
    Given a deterministic in-memory recall harness
    And recall candidates include a recent anchor and older distractor
    When the user asks a pronoun temporal follow-up "how long ago was it yesterday"
    Then the temporal anaphora bridge selects the anchor before rerank
    And the bridge emits elapsed delta and yesterday window details

  Scenario: observe and stabilize happen before route authority
    Given a canonical stage harness with a raw utterance "My name is Sebastian"
    When canonical observe encode and stabilize execute
    Then the stage artifacts include a typed turn observation
    And stabilization provides same-turn exclusion doc ids before intent resolve

