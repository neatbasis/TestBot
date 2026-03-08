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
    And the response includes deterministic citation-context formatting

  Scenario: progressive assist fallback path
    Given a deterministic in-memory recall harness
    And eval cases are loaded from "eval/cases.jsonl"
    When the user asks about eval case "no-memory-match"
    Then the assistant returns an assistive fallback response

  Scenario: equivalent candidates remain ambiguous after tie-break
    Given a deterministic in-memory recall harness
    When equivalent top candidates remain after tie-break
    Then the assistant returns a bridging clarification response

  Scenario: pronoun temporal follow-up resolves anchor before routing
    Given a deterministic in-memory recall harness
    And recall candidates include a recent anchor and older distractor
    When the user asks a pronoun temporal follow-up "how long ago was it yesterday"
    Then the temporal anaphora bridge selects the anchor before rerank
    And the bridge emits elapsed delta and yesterday window details

  Scenario: observe and stabilize happen before route authority
    Given a canonical stage harness with a raw utterance "My name is Sebastian"
    When canonical stages execute stabilize then intent resolve then retrieve
    Then stabilization artifacts are persisted before route authority assignment
    And route authority cannot be finalized until stabilization outputs exist

  Scenario: observe.turn stores user claims only as observation artifacts in-turn
    Given a canonical memory claim harness with claim "My favorite color is green"
    When observe.turn captures the claim for turn "turn-memory-1"
    And retrieval executes in the same turn before answer.commit
    Then observed artifact ids should be "obs-turn-memory-1-claim-1"
    And committed memory ids should be empty
    And same-turn retrieval should not return committed memory id "mem-turn-memory-1-claim-1"

  Scenario: committed claims become retrievable memory only in a later turn
    Given a canonical memory claim harness with claim "My favorite color is green"
    When observe.turn captures the claim for turn "turn-memory-1"
    And answer.commit persists the observed claim as memory id "mem-turn-memory-1-claim-1"
    And retrieval executes in a later turn "turn-memory-2"
    Then observed artifact ids should be "obs-turn-memory-1-claim-1"
    And committed memory ids should include "mem-turn-memory-1-claim-1"
    And later-turn retrieval should return committed memory id "mem-turn-memory-1-claim-1"

  Scenario: same-turn retrieval that returns a just-observed claim is rejected
    Given a canonical memory claim harness with claim "My favorite color is green"
    When observe.turn captures the claim for turn "turn-memory-1"
    And retrieval incorrectly returns just-observed artifact id "obs-turn-memory-1-claim-1" in the same turn
    Then same-turn retrieval should be rejected as invalid durable memory


  Scenario: segment-aware continuity groups multi-turn self-profile memory
    Given derived memory segments for follow-up self-profile turns
    Then the segment id remains stable across those turns

  Scenario: strata-aware retrieval prefers semantic memory over episodic utterance
    Given a segment with semantic and episodic memory candidates
    When evidence is bundled for policy consumption
    Then semantic memory is retained as canonical evidence for that segment
    And raw episodic utterance evidence for that segment is de-prioritized


  @ISSUE-0013 @AC-0013-01 @AC-0013-03 @AC-0013-05 @AC-0013-10
  Scenario Outline: canonical pre-route artifacts are established for ISSUE-0013 regression utterances
    Given a canonical stage harness with a raw utterance "<utterance>"
    When canonical observe encode and stabilize execute
    Then the stage artifacts include a typed turn observation
    And stabilization provides same-turn exclusion doc ids before intent resolve

    Examples:
      | utterance                               |
      | Hi! I'm Sebastian                       |
      | The memory today                        |
      | How log ago did I ask you something?   |
