@Rule:CitationContract @Role:Resident @Priority:High @fast
Feature: Memory recall behavior
  In order to trust responses grounded in memory
  As a resident
  I want cited answers when memory is sufficient and exact fallback when it is not

  Scenario: cited memory-grounded answer path
    Given a deterministic in-memory recall harness
    And eval cases are loaded from "eval/cases.jsonl"
    When the user asks about eval case "sleep-followup"
    Then the assistant returns a memory-grounded answer
    And the answer includes citation fields "doc_id" and "ts"

  Scenario: exact fallback path
    Given a deterministic in-memory recall harness
    And eval cases are loaded from "eval/cases.jsonl"
    When the user asks about eval case "no-memory-match"
    Then the assistant responds exactly "I don't know from memory."
