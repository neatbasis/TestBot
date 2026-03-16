@Owner:testbot @Rule:IntentGrounding @Role:Resident @Priority:High @fast
Feature: Intent-specific grounding and provenance behavior
  In order to keep non-memory responses trustworthy
  As a resident
  I want intent-aware answers to carry explicit grounding and basis statements

  @ISSUE-0008 @AC-0008-01
  Scenario: knowledge question with memory miss returns labeled general answer and clarification
    Given an intent response harness
    When a knowledge question misses memory context
    Then the assistant returns a labeled general answer with clarification
    And the rendered answer should include semantic markers
      | marker                  |
      | general_knowledge_label |
      | clarification_prompt    |
    And the response records general-knowledge provenance and basis
    And the provenance and basis should include "GENERAL_KNOWLEDGE" and "General-knowledge basis:"

  @ISSUE-0008 @AC-0008-02
  Scenario: meta question what did I ask uses chat-history grounding
    Given an intent response harness
    When the user asks "what did I ask?"
    Then the assistant replies from chat history
    And the rendered answer should include semantic markers
      | marker             |
      | chat_history_recap |
    And the response records chat-history provenance and basis
    And the provenance and basis should include "CHAT_HISTORY" and "chat history"

  @ISSUE-0008 @AC-0008-03
  Scenario: relevance question returns summarized relevance with basis statement
    Given an intent response harness
    When the user asks a relevance question
    Then the assistant returns a summarized relevance answer
    And the rendered answer should include semantic markers
      | marker          |
      | relevance_label |
    And the response includes a relevance basis assertion
    And the provenance and basis should include "CHAT_HISTORY" and "Relevance summary basis:"

  @Rule:SourceBackedAnswer
  @ISSUE-0008 @AC-0008-04
  Scenario: source-backed knowing answer includes source citation provenance
    Given an intent response harness
    When the user asks a source-backed knowing question
    Then the assistant returns a source-backed answer with citation
    And the provenance and basis should include "MEMORY" and "source evidence"
    And the source provenance includes "calendar://work/event-42" and "calendar"

  @Rule:SourceBackedAnswer
  @Rule:FallbackSemantics
  @ISSUE-0008 @AC-0008-05
  Scenario: source confidence insufficient triggers progressive unknowing response
    Given an intent response harness
    When source confidence is insufficient for a knowing answer
    Then the assistant returns a progressive unknowing response
    And the rendered answer should include semantic markers
      | marker      |
      | uncertainty |
      | safe_action |
    And the provenance and basis should include "UNKNOWN" and "Trivial fallback"
    And the fallback reason should be "non_memory_low_source_confidence"

  @Rule:SourceBackedAnswer
  @Rule:FallbackSemantics
  @ISSUE-0008 @AC-0008-06
  Scenario: low-confidence source evidence avoids direct source-backed claims
    Given an intent response harness
    When source evidence remains low-confidence after retrieval
    Then the assistant returns a progressive unknowing response
    And the response should not include "source_uri:"
    And the provenance and basis should include "UNKNOWN" and "Trivial fallback"
    And the fallback reason should be "insufficient_reliable_memory"

  @Rule:SourceBackedAnswer
  @ISSUE-0008 @AC-0008-07
  Scenario: assembled answer object combines memory and source evidence with explicit fields
    Given an intent response harness
    When memory and source evidence are assembled into a knowing response
    Then the assembled answer object includes memory and source evidence references

  @Rule:SourceBackedAnswer
  @ISSUE-0008 @AC-0008-08
  Scenario: assembled answer object enforces required attribution fields by evidence type
    Given an intent response harness
    When memory and source evidence are assembled into a knowing response
    Then the assembled answer object includes required attribution fields for each evidence type

  @Rule:SourceBackedAnswer
  @ISSUE-0008 @AC-0008-09
  Scenario: assembled answer object resolves evidence conflicts to clarification posture
    Given an intent response harness
    When assembled evidence inputs disagree for the same intent response
    Then the assembled answer object records conflict-resolution fallback behavior

  @Rule:AmbiguityHandling
  @Rule:FallbackSemantics
  @ISSUE-0008 @AC-0008-10
  Scenario: conflicting source evidence asks a targeted clarifying question
    Given an intent response harness
    When source evidence conflicts across candidate records
    Then the assistant asks a targeted clarifying question
    And the rendered answer should include normative phrase "Which person, event, or time window should I focus on?"
    And the provenance and basis should include "UNKNOWN" and "Trivial fallback"
    And the fallback reason should be "ambiguous_memory_candidates_without_ask"


  @ISSUE-0008 @AC-0008-11
  Scenario: affirmation follow-up preserves clarification intent continuity
    Given an intent response harness
    When the user asks to ask something via satellite and follows up with "yes"
    Then the resolved follow-up intent should preserve capabilities help continuity

  @ISSUE-0008 @AC-0008-12
  Scenario: delayed yes after topic shift does not preserve stale clarification continuity
    Given an intent response harness
    And a prior clarification commit-state harness for capabilities help
    When a topic shift turn is committed before delayed follow-up "yes"
    Then delayed follow-up should re-evaluate instead of preserving prior clarification intent
    And commit-state transitions should clear stale clarification continuity at the topic-shift boundary

  @ISSUE-0008 @AC-0008-13
  Scenario: hostile or sarcastic affirmation does not auto-preserve clarification continuity
    Given an intent response harness
    And a prior clarification commit-state harness for capabilities help
    When a hostile follow-up "yeah sure whatever" is evaluated against prior clarification state
    Then hostile affirmation should not preserve prior clarification intent
    And commit-state transitions should clear clarification obligations at the hostile follow-up boundary



  @ISSUE-0008 @AC-0008-14
  Scenario: non-memory question with no ambiguity does not trigger clarifier
    Given an intent response harness
    When a non-memory knowledge question has no ambiguity
    Then the response should remain in direct knowledge-answer flow
    And the response should not use clarifier mode
    And the rendered answer should include semantic markers
      | marker                  |
      | general_knowledge_label |

  @ISSUE-0008 @AC-0008-15
  Scenario: definitional prompt uses retrieval-enabled branch logging
    Given an intent response harness
    When the user asks a definitional knowledge prompt in runtime loop
    Then retrieval branch logging should show memory retrieval with unskipped candidates

  @ISSUE-0008 @AC-0008-30
  Scenario: definitional prompt with initial empty retrieval performs bounded sync retry once
    Given an intent response harness
    When a definitional knowledge prompt has initial empty retrieval and async continuation is off
    Then retrieval retry logging should show one bounded sync retry
    And fallback outcome should remain deterministic when evidence stays empty

  @ISSUE-0008 @AC-0008-16
  Scenario: conversational prompt avoids knowledge retrieval branch logging
    Given an intent response harness
    When the user asks a conversational prompt in runtime loop
    Then retrieval branch logging should show direct answer with skipped candidates


  @ISSUE-0008 @AC-0008-17
  Scenario: self-identity recall follow-up forces retrieval before direct-answer shortcut
    Given an intent response harness
    When the user says "Hi! I'm sebastian" then asks "Who am I?"
    Then identity recall guard should force memory retrieval branch evaluation


  @ISSUE-0008 @AC-0008-18
  Scenario: retrieval policy distinguishes empty evidence from scored-empty candidates
    Given an intent response harness
    When retrieval policy evaluates empty and scored-empty evidence states
    Then retrieval policy should record empty-evidence and scored-empty postures distinctly

  @ISSUE-0008 @AC-0008-19
  Scenario: memory-recall follow-up scored-empty keeps clarification class and memory branch
    Given an intent response harness
    When memory-recall follow-up is evaluated under scored-empty evidence
    Then memory-recall follow-up policy should keep clarification decision class and memory retrieval branch


  @ISSUE-0008 @AC-0008-20
  Scenario: continuity-sensitive routing preserves prior intent only for affirmative clarifier follow-ups
    Given an intent response harness
    When intent continuity is evaluated for affirmative and non-affirmative follow-ups
    Then continuity routing should preserve prior intent only for affirmative clarification follow-ups

  @ISSUE-0008 @AC-0008-21
  Scenario: encode candidates retain multiple plausible intents before routing
    Given an intent response harness
    When encode candidates include multiple plausible intents pre-route
    Then encode candidates should retain multiple intents without premature collapse

  @ISSUE-0008 @AC-0008-22
  Scenario: encode candidates normalize duplicate candidate ids deterministically
    Given an intent response harness
    When encode candidates include duplicate candidate ids
    Then encode candidates should dedupe candidate ids deterministically

  @ISSUE-0008 @AC-0008-23
  Scenario: encode candidates reject malformed provenance before downstream stages
    Given an intent response harness
    When encode candidates include null or malformed provenance
    Then malformed provenance candidates should be quarantined before downstream stages

  @ISSUE-0008 @AC-0008-24
  Scenario: control phrasing wins over ambiguous help and memory language
    Given an intent response harness
    When the user asks an ambiguous control-help-memory phrase
    Then the utterance should route to control intent deterministically

  @ISSUE-0008 @AC-0008-25
  Scenario: capabilities satellite phrasing wins over meta-conversation cue
    Given an intent response harness
    When the user asks an ambiguous satellite-versus-meta phrase
    Then the utterance should route to capabilities help intent deterministically

  @Rule:AmbiguityHandling
  @ISSUE-0008 @AC-0008-26
  Scenario: unmatched ambiguous phrasing falls back to knowledge question
    Given an intent response harness
    When the user asks an unmatched ambiguous phrase
    Then the utterance should route to knowledge-question fallback deterministically

  @ISSUE-0008 @AC-0008-27
  Scenario Outline: taxonomy contract maps ambiguous prompts to deterministic typed intents
    Given an intent response harness
    When intent taxonomy mapping is evaluated for ambiguous prompts
      | prompt   | expected_intent   | expected_pathway   | temporal   | memory   | capability   | control   |
      | <prompt> | <expected_intent> | <expected_pathway> | <temporal> | <memory> | <capability> | <control> |
    Then typed intent object fields should match the taxonomy mapping table

    Examples:
      | prompt                                             | expected_intent   | expected_pathway | temporal | memory | capability | control |
      | stop, can you help me remember what did I ask?     | control           | control          | false    | false  | false      | true    |
      | use satellite about this chat                      | capabilities_help | capabilities     | false    | false  | true       | false   |
      | what did I ask about satellite earlier             | memory_recall     | memory_recall    | false    | true   | true       | false   |
      | how many minutes ago did we talk before?           | time_query        | time_query       | true     | true   | false      | false   |
      | this seems mixed and maybe relevant                | knowledge_question| non_memory       | false    | false  | false      | false   |

  @ISSUE-0008 @AC-0008-28
  Scenario Outline: taxonomy contract rejects invalid class and facet combinations
    Given an intent response harness
    When typed intent objects are validated for class and facet compatibility
      | intent_class   | temporal   | memory   | capability   | control   | expected_reason   |
      | <intent_class> | <temporal> | <memory> | <capability> | <control> | <expected_reason> |
    Then invalid typed intent objects should be rejected with deterministic reasons

    Examples:
      | intent_class       | temporal | memory | capability | control | expected_reason                      |
      | control            | false    | false  | true       | true    | control_cannot_include_other_facets |
      | capabilities_help  | false    | false  | false      | false   | capabilities_help_requires_capability|
      | meta_conversation  | true     | false  | false      | false   | meta_cannot_include_temporal_memory |
      | time_query         | false    | true   | false      | false   | time_query_requires_temporal        |
      | knowledge_question | false    | false  | false      | true    | control_facet_requires_control_intent|

  @Rule:AmbiguityHandling
  @ISSUE-0008 @AC-0008-29
  Scenario: ambiguous prompt enumerates explanation space before convergence
    Given an intent response harness
    When the user asks an ambiguous prompt requiring divergent analysis
    Then the assistant enumerates plausible explanation spaces before converging
    And the rendered answer should include semantic markers
      | marker                    |
      | possible_explanations_tag |
      | converged_recommendation  |

  @ISSUE-0008 @AC-0008-30
  Scenario: multi-framework prompt switches perspectives before final synthesis
    Given an intent response harness
    When the user asks for a multi-framework perspective switch
    Then the assistant presents multiple frameworks and a synthesized conclusion
    And the rendered answer should include semantic markers
      | marker                    |
      | framework_systems         |
      | framework_behavioral      |
      | synthesis_label           |


  @ISSUE-0008 @AC-0008-31
  Scenario: self-identification utterance routes to non-knowledge intent
    Given an intent response harness
    When the user provides a self-identification utterance
    Then the utterance should route to non-knowledge social intent deterministically

  @ISSUE-0008 @AC-0008-32
  Scenario: self-identification rewrite preserves user discourse object
    Given an intent response harness
    When the user provides a self-identification utterance for rewrite
    Then rewrite output should preserve identity declaration wording
    And rewrite output should not be assistant-focused for self-identification input

  @ISSUE-0008 @AC-0008-33
  Scenario: greeting utterance routes to non-knowledge intent
    Given an intent response harness
    When the user provides a greeting utterance
    Then the utterance should route to non-knowledge social intent deterministically

  @ISSUE-0008 @AC-0008-34
  Scenario: say-hello command routes to command intent
    Given an intent response harness
    When the user provides a say-hello command
    Then the utterance should route to control intent deterministically

  @Rule:TemporalRouting
  @ISSUE-0008 @AC-0008-35
  Scenario: mixed temporal and memory phrasing preserves time intent with memory facet visibility
    Given an intent response harness
    When the user asks a mixed temporal-memory phrase
    Then the utterance should route to time-query intent with temporal and memory facets

  @ISSUE-0008 @AC-0008-36
  Scenario: capabilities in context preserves knowledge routing with capability facet
    Given an intent response harness
    When the user asks a capabilities-in-context phrase
    Then the utterance should route to knowledge intent with capability facet

  @ISSUE-0008 @AC-0008-37
  Scenario: typed decision outcomes are selected deterministically
    Given an intent response harness
    When policy decision objects are resolved from typed evidence states
    Then the decision outcomes should include "answer_from_memory" and "answer_general_knowledge_labeled"
    And the decision outcomes should include "ask_for_clarification" and "continue_repair_reconstruction"

  @ISSUE-0008 @AC-0008-38
  Scenario: typed empty and scored-empty evidence states map to distinct fallback behaviors
    Given an intent response harness
    When typed fallback contracts are resolved for empty and scored-empty evidence
    Then typed evidence states should remain distinct for empty and scored-empty
    And the typed evidence-state mapping should include decision class "ask_for_clarification" and provenance label "UNKNOWN" for "E.empty"
    And the typed evidence-state mapping should include decision class "ask_for_clarification" and provenance label "UNKNOWN" for "E.scored_empty"
    And the typed evidence-state mapping should include fallback strategy "ASK_CLARIFIER" for "E.empty"
    And the typed evidence-state mapping should include fallback strategy "ANSWER_UNKNOWN" for "E.scored_empty"
    And the typed evidence-state mapping should include fallback strategy "OFFER_ASSIST_ALTERNATIVES" for "E.scored_empty_non_memory"


  @ISSUE-0008 @AC-0008-39
  Scenario: note-taking utterance preserves direct-answer assist contract
    Given an intent response harness
    When note-taking utterance contract probe is resolved through canonical decisioning
    Then the canonical contract should resolve intent "meta_conversation" retrieval branch "direct_answer" decision class "answer_general_knowledge_labeled" fallback action "ANSWER_GENERAL_KNOWLEDGE" and answer mode "assist"

  @ISSUE-0008 @AC-0008-40
  Scenario: memory-write utterance preserves direct-answer assist contract
    Given an intent response harness
    When memory-write utterance contract probe is resolved through canonical decisioning
    Then the canonical contract should resolve intent "meta_conversation" retrieval branch "direct_answer" decision class "answer_general_knowledge_labeled" fallback action "ANSWER_GENERAL_KNOWLEDGE" and answer mode "assist"

  @ISSUE-0008 @AC-0008-41
  Scenario: intent-heavy routing waits for stabilization outputs before authority finalization
    Given a canonical stage harness with a raw utterance "could you ask satellite to message sebastian"
    When canonical stages execute stabilize then intent resolve then retrieve
    Then stabilization artifacts are persisted before route authority assignment
    And route authority cannot be finalized until stabilization outputs exist
