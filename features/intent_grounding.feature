@Rule:IntentGrounding @Role:Resident @Priority:High @fast
Feature: Intent-specific grounding and provenance behavior
  In order to keep non-memory responses trustworthy
  As a resident
  I want intent-aware answers to carry explicit grounding and basis statements

  Scenario: knowledge question with memory miss returns labeled general answer and clarification
    Given an intent response harness
    When a knowledge question misses memory context
    Then the assistant returns a labeled general answer with clarification
    And the response records general-knowledge provenance and basis

  Scenario: meta question what did I ask uses chat-history grounding
    Given an intent response harness
    When the user asks "what did I ask?"
    Then the assistant replies from chat history
    And the response records chat-history provenance and basis

  Scenario: relevance question returns summarized relevance with basis statement
    Given an intent response harness
    When the user asks a relevance question
    Then the assistant returns a summarized relevance answer
    And the response includes a relevance basis assertion
