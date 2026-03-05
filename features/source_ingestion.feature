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
