@Rule:CapabilitiesHelp @Role:Resident @Priority:High @fast
Feature: Capabilities help responses
  In order to understand what the assistant can do
  As a resident
  I want help/capabilities prompts to return truthful runtime capability summaries

  Scenario Outline: HA unavailable with CLI fallback returns degraded/unavailable capability statements
    Given a capabilities help prompt "<prompt>"
    When the stage answer flow handles capabilities under HA unavailable with CLI fallback
    Then the prompt is classified as capabilities help intent
    And the answer includes "Home Assistant actions: unavailable"
    And the answer includes "can continue in cli mode (CLI fallback is active)"
    And the answer includes "cannot run satellite actions while Home Assistant is unavailable"
    And the answer includes "Ask/disambiguation flow: degraded"
    And the answer includes "Debug visibility: unavailable"

    Examples:
      | prompt          |
      | what can you do |
      | capabilities    |

  Scenario: HA available with satellite enabled returns available capability statements
    Given a capabilities help prompt "what can you do"
    When the stage answer flow handles capabilities under HA available with satellite enabled
    Then the prompt is classified as capabilities help intent
    And the answer includes "Home Assistant actions: available"
    And the answer includes "can use satellite ask/speak actions"
    And the answer includes "Ask/disambiguation flow: available"
    And the answer includes "Debug visibility: available"
    And the answer includes "Memory recall: available"
    And the answer includes "General explanations: available"
