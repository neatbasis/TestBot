@Rule:CapabilitiesHelp @Role:Resident @Priority:High @fast
Feature: Capabilities help responses
  In order to understand what the assistant can do
  As a resident
  I want help/capabilities prompts to return a stable capability summary

  Scenario Outline: capabilities/meta-help intent returns stable summary independent of memory
    Given a capabilities help prompt "<prompt>"
    When the stage answer flow handles the prompt with and without memory hits
    Then the prompt is classified as capabilities help intent
    And both answers return the stable capability summary
    And the summary includes "memory-grounded recall"
    And the summary includes "general explanation support"
    And the summary includes "clarifying-question support"
    And the summary includes "degraded message when unavailable"
    And the summary includes "debug visibility only when debug mode is enabled"

    Examples:
      | prompt           |
      | what can you do  |
      | help             |
      | capabilities     |
