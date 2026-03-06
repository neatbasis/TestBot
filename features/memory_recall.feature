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
