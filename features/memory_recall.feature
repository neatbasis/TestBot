@Rule:CitationContract @Role:Resident @Priority:High @fast
Feature: Memory recall behavior
  In order to trust responses grounded in memory
  As a resident
  I want cited answers when memory is sufficient and exact fallback when it is not

  Scenario: cited memory-grounded answer path
    Given a deterministic in-memory recall harness
    And deterministic memory fixtures are loaded
    When the user asks "When is garbage pickup?"
    Then the assistant returns a memory-grounded answer
    And the answer includes citation fields "doc_id" and "ts"

  Scenario: exact fallback path
    Given a deterministic in-memory recall harness
    And deterministic memory fixtures are loaded
    When the user asks "What is the HOA gate code?"
    Then the assistant responds exactly "I don't know from memory."
