@Rule:TimeAwareness @Rule:TemporalRouting @Role:Resident @Priority:High @fast
Feature: Time-aware routing and deterministic responses
  In order to answer simple temporal questions deterministically
  As a resident
  I want time-intent questions routed through a dedicated assist mode

  Scenario: elapsed minutes from previous user turn
    Given a frozen time in Europe/Helsinki
    When the user asks how many minutes ago the previous message was
    Then the response should mention elapsed minutes from the previous turn

  Scenario: resolve tomorrow in Europe/Helsinki
    Given a frozen time in Europe/Helsinki
    When the user asks what is tomorrow
    Then the response should contain the Helsinki tomorrow date
