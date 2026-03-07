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

  Scenario: source-backed knowing answer includes source citation provenance
    Given an intent response harness
    When the user asks a source-backed knowing question
    Then the assistant returns a source-backed answer with citation
    And the provenance and basis should include "MEMORY" and "source evidence"
    And the source provenance includes "calendar://work/event-42" and "calendar"

  Scenario: source confidence insufficient triggers progressive unknowing response
    Given an intent response harness
    When source confidence is insufficient for a knowing answer
    Then the assistant returns a progressive unknowing response
    And the response should include explicit uncertainty language
    And the response should include a safe action path
    And the provenance and basis should include "UNKNOWN" and "Trivial fallback"

  Scenario: low-confidence source evidence avoids direct source-backed claims
    Given an intent response harness
    When source evidence remains low-confidence after retrieval
    Then the assistant returns a progressive unknowing response
    And the response should not include "source_uri:"
    And the provenance and basis should include "UNKNOWN" and "Trivial fallback"

  Scenario: conflicting source evidence asks a targeted clarifying question
    Given an intent response harness
    When source evidence conflicts across candidate records
    Then the assistant asks a targeted clarifying question
    And the response should include "Which person, event, or time window should I focus on?"
    And the provenance and basis should include "UNKNOWN" and "Trivial fallback"


  Scenario: affirmation follow-up preserves clarification intent continuity
    Given an intent response harness
    When the user asks to ask something via satellite and follows up with "yes"
    Then the resolved follow-up intent should preserve capabilities help continuity



  Scenario: non-memory question with no ambiguity does not trigger clarifier
    Given an intent response harness
    When a non-memory knowledge question has no ambiguity
    Then the response should remain in direct knowledge-answer flow
    And the response should not use clarifier mode
    And the response should include "General definition (not from your memory):"

  Scenario: definitional prompt uses retrieval-enabled branch logging
    Given an intent response harness
    When the user asks a definitional knowledge prompt in runtime loop
    Then retrieval branch logging should show memory retrieval with unskipped candidates

  Scenario: conversational prompt avoids knowledge retrieval branch logging
    Given an intent response harness
    When the user asks a conversational prompt in runtime loop
    Then retrieval branch logging should show direct answer with skipped candidates

  Scenario: control phrasing wins over ambiguous help and memory language
    Given an intent response harness
    When the user asks an ambiguous control-help-memory phrase
    Then the utterance should route to control intent deterministically

  Scenario: capabilities satellite phrasing wins over meta-conversation cue
    Given an intent response harness
    When the user asks an ambiguous satellite-versus-meta phrase
    Then the utterance should route to capabilities help intent deterministically

  Scenario: unmatched ambiguous phrasing falls back to knowledge question
    Given an intent response harness
    When the user asks an unmatched ambiguous phrase
    Then the utterance should route to knowledge-question fallback deterministically

  Scenario: ambiguous prompt enumerates explanation space before convergence
    Given an intent response harness
    When the user asks an ambiguous prompt requiring divergent analysis
    Then the assistant enumerates plausible explanation spaces before converging
    And the response should include "Possible explanations:"
    And the response should include "Converged recommendation:"

  Scenario: multi-framework prompt switches perspectives before final synthesis
    Given an intent response harness
    When the user asks for a multi-framework perspective switch
    Then the assistant presents multiple frameworks and a synthesized conclusion
    And the response should include "Framework: systems"
    And the response should include "Framework: behavioral"
    And the response should include "Synthesis:"


  Scenario: self-identification utterance routes to non-knowledge intent
    Given an intent response harness
    When the user provides a self-identification utterance
    Then the utterance should route to non-knowledge social intent deterministically

  Scenario: greeting utterance routes to non-knowledge intent
    Given an intent response harness
    When the user provides a greeting utterance
    Then the utterance should route to non-knowledge social intent deterministically

  Scenario: say-hello command routes to command intent
    Given an intent response harness
    When the user provides a say-hello command
    Then the utterance should route to control intent deterministically

  Scenario: mixed temporal and memory phrasing preserves time intent with memory facet visibility
    Given an intent response harness
    When the user asks a mixed temporal-memory phrase
    Then the utterance should route to time-query intent with temporal and memory facets

  Scenario: capabilities in context preserves knowledge routing with capability facet
    Given an intent response harness
    When the user asks a capabilities-in-context phrase
    Then the utterance should route to knowledge intent with capability facet
