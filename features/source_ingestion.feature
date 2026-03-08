@Rule:SourceBackedKnowing @Rule:SourceBackedAnswer @Role:Resident @Priority:High @fast
Feature: Source-backed ingestion behavior
  In order to trust answers grounded in synced sources
  As a resident
  I want deterministic source evidence provenance and trust-tier-aware fallback

  @ISSUE-0013 @AC-0013-01
  Scenario: source-backed knowing answer includes evidence attribution
    Given a deterministic source-ingestion harness
    When the assistant answers using source evidence with trust tier "verified"
    Then the provenance includes source evidence references and attribution fields

  @ISSUE-0013 @AC-0013-02
  Scenario: low-trust source evidence triggers fallback
    Given a deterministic source-ingestion harness
    When the assistant only has source evidence with trust tier "low"
    Then the assistant returns trust-tier-aware fallback response

  @ISSUE-0013 @AC-0013-03
  Scenario: assembled answer combines memory and source evidence in structured payload
    Given a deterministic source-ingestion harness
    When the assistant assembles an answer from memory and source evidence
    Then the assembled payload records both memory and source evidence references

  @ISSUE-0013 @AC-0013-04
  Scenario: assembled payload includes required attribution fields per evidence type
    Given a deterministic source-ingestion harness
    When the assistant assembles an answer from memory and source evidence
    Then the assembled payload includes required attribution fields for each evidence type

  @ISSUE-0013 @AC-0013-05
  Scenario: conflicting evidence resolves to clarification without unsupported attribution
    Given a deterministic source-ingestion harness
    When memory and source evidence disagree for the same question
    Then the assembled payload resolves the conflict with clarification metadata
