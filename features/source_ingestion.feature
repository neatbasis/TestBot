@Rule:SourceBackedKnowing @Role:Resident @Priority:High @fast
Feature: Source-backed ingestion behavior
  In order to trust answers grounded in synced sources
  As a resident
  I want deterministic source evidence provenance and trust-tier-aware fallback

  Scenario: source-backed knowing answer includes evidence attribution
    Given a deterministic source-ingestion harness
    When the assistant answers using source evidence with trust tier "verified"
    Then the provenance includes source evidence references and attribution fields

  Scenario: low-trust source evidence triggers fallback
    Given a deterministic source-ingestion harness
    When the assistant only has source evidence with trust tier "low"
    Then the assistant returns trust-tier-aware fallback response

  Scenario: assembled answer combines memory and source evidence in structured payload
    Given a deterministic source-ingestion harness
    When the assistant assembles an answer from memory and source evidence
    Then the assembled payload records both memory and source evidence references

  Scenario: assembled payload includes required attribution fields per evidence type
    Given a deterministic source-ingestion harness
    When the assistant assembles an answer from memory and source evidence
    Then the assembled payload includes required attribution fields for each evidence type

  Scenario: conflicting evidence resolves to clarification without unsupported attribution
    Given a deterministic source-ingestion harness
    When memory and source evidence disagree for the same question
    Then the assembled payload resolves the conflict with clarification metadata
