@Rule:IntentGrounding @Role:Resident @Priority:High @fast
Feature: Intent-specific grounding and provenance behavior
  In order to keep non-memory responses trustworthy
  As a resident
  I want intent-aware answers to carry explicit grounding and basis statements

  Scenario: knowledge question with memory miss returns labeled general answer and clarification
    Given an intent response harness
    When a knowledge question misses memory context
    Then the assistant returns a labeled general answer with clarification
    And the response should include "General definition (not from your memory):"
    And the response should include "Can you clarify which domain"
    And the response records general-knowledge provenance and basis
    And the provenance and basis should include "GENERAL_KNOWLEDGE" and "General-knowledge basis:"

  Scenario: meta question what did I ask uses chat-history grounding
    Given an intent response harness
    When the user asks "what did I ask?"
    Then the assistant replies from chat history
    And the response should include "You asked about ontology earlier in this chat."
    And the response records chat-history provenance and basis
    And the provenance and basis should include "CHAT_HISTORY" and "chat history"

  Scenario: relevance question returns summarized relevance with basis statement
    Given an intent response harness
    When the user asks a relevance question
    Then the assistant returns a summarized relevance answer
    And the response should include "Relevant summary:"
    And the response includes a relevance basis assertion
    And the provenance and basis should include "CHAT_HISTORY" and "Relevance summary basis:"
