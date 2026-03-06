@Rule:AnswerContract @Role:Resident @Priority:High @fast
Feature: Answer citation contract enforcement
  In order to prevent unsupported factual claims
  As a resident
  I want uncited factual responses to be rejected

  Scenario: rejection of uncited factual response from eval pattern
    Given an uncited factual candidate from eval case "project-deadline"
    When the answer contract validator checks the candidate
    Then the candidate is rejected

  Scenario: disallowed unlabeled general-knowledge factual output
    Given a general-knowledge factual candidate without marker text
    And the general-knowledge confidence gate does not pass
    When the general-knowledge contract validator checks the candidate
    Then the general-knowledge candidate is rejected

  Scenario: allowed labeled general-knowledge output when confidence gate passes
    Given a general-knowledge factual candidate with marker text
    And the general-knowledge confidence gate passes
    When the general-knowledge contract validator checks the candidate
    Then the general-knowledge candidate is accepted

  Scenario: non-memory general-knowledge fallback stays knowledge-safe
    Given a non-memory knowledge question "what is ontology?"
    And an unlabeled general-knowledge draft answer with failed confidence gate
    When stage answer enforces the general-knowledge contract
    Then the final answer should be knowledge-safe fallback
    And the final answer should include explicit uncertainty language
    And the final answer should include a safe action path
    And the final answer should not ask "Which person, event, or time window should I focus on?"
    And the response records knowledge-safe fallback provenance transparency
