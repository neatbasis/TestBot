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

  Scenario: ambiguous memory recall uses ask route when ask capability is available
    Given an answer policy input with intent "memory_recall", context confidence true, ambiguity true, and memory hit count 2
    And ask capability status is "ask_available"
    When the answer routing policy resolves the request
    Then the fallback action should be "ROUTE_TO_ASK"
    And the canonical response token should be "ROUTE_TO_ASK_ANSWER"

  Scenario: low-confidence non-memory fallback maps to uncertainty token
    Given an answer policy input with intent "non_memory", context confidence false, ambiguity false, and memory hit count 0
    And ask capability status is "ask_unavailable"
    And source confidence is 0.2
    When the answer routing policy resolves the request
    Then the fallback action should be "ANSWER_UNKNOWN"
    And the canonical response token should be "NON_KNOWLEDGE_UNCERTAINTY_ANSWER"
    And the policy rationale includes considered alternatives with rejection reasons
    And the policy rationale fallback reason should be "non_memory_low_source_confidence"

  Scenario: memory recall without confident hit offers assist alternatives
    Given an answer policy input with intent "memory_recall", context confidence false, ambiguity false, and memory hit count 0
    And ask capability status is "ask_unavailable"
    When the answer routing policy resolves the request
    Then the fallback action should be "OFFER_CAPABILITY_ALTERNATIVES"
    And the canonical response token should be "ASSIST_ALTERNATIVES_ANSWER"

  Scenario: low-confidence recall debug emits transparent observation and policy layers
    Given a low-confidence recall pipeline state with ambiguous references
    When the structured debug payload is built for memory recall
    Then the debug payload includes explicit observation and policy layers
    And the fallback decision includes considered alternatives and rejection reasons
    And rejected-turn diagnostics include nearest failure gate details
    And debug counterfactuals include threshold and alternate-routing checks

  Scenario: stabilization persists candidate facts before route authority
    Given a canonical stage harness with a raw utterance "My name is Sebastian"
    When canonical observe encode and stabilize execute
    Then stabilization candidate facts include "user_name" as "Sebastian"


  Scenario: known fact must not degrade to general-knowledge fallback
    Given a memory recall question with retrieval evidence available
    And a canonical decision object class "answer_from_memory"
    When stage answer runs with canonical decision authority
    Then the final answer remains memory-grounded
    And the fallback action remains memory-grounded for canonical routing


  Scenario: canonical routing authority is assigned only after stabilization
    Given a canonical stage harness with a raw utterance "hello there"
    When canonical stages execute stabilize then intent resolve then retrieve
    Then stabilization artifacts are persisted before route authority assignment
    And route authority cannot be finalized until stabilization outputs exist
