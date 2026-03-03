@Rule:AnswerContract @Role:Resident @Priority:High @fast
Feature: Answer citation contract enforcement
  In order to prevent unsupported factual claims
  As a resident
  I want uncited factual responses to be rejected

  Scenario: rejection of uncited factual response
    Given an uncited factual candidate answer "Garbage pickup is every Tuesday morning."
    When the answer contract validator checks the candidate
    Then the candidate is rejected
