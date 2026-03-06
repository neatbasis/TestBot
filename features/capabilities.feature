@Rule:CapabilitiesHelp @Role:Resident @Priority:High @fast
Feature: Capabilities help responses
  In order to understand what the assistant can do
  As a resident
  I want help/capabilities prompts to return truthful runtime capability summaries

  Scenario Outline: HA unavailable with CLI fallback keeps text clarification available while satellite ask is unavailable
    Given a capabilities help prompt "<prompt>"
    When the stage answer flow handles capabilities under HA unavailable with CLI fallback
    Then the prompt is classified as capabilities help intent
    And the answer includes "Home Assistant satellite actions: unavailable"
    And the answer includes "can continue in cli mode (CLI fallback is active)"
    And the answer includes "cannot run satellite actions while Home Assistant is unavailable"
    And the answer includes "Clarification/disambiguation: available"
    And the answer includes "text clarification still available in CLI"
    And the answer includes "interactive satellite ask flow unavailable in CLI mode"
    And the answer includes "Satellite ask loop: unavailable"
    And the answer includes "Debug visibility: disabled (set TESTBOT_DEBUG=1 to enable)"

    Examples:
      | prompt          |
      | what can you do |
      | capabilities    |

  Scenario: HA available with satellite enabled returns available capability statements
    Given a capabilities help prompt "what can you do"
    When the stage answer flow handles capabilities under HA available with satellite enabled
    Then the prompt is classified as capabilities help intent
    And the answer includes "Home Assistant satellite actions: available"
    And the answer includes "can use satellite speak/start-conversation actions"
    And the answer includes "Satellite ask loop: available"
    And the answer includes "Debug visibility: enabled (TESTBOT_DEBUG=1)"
    And the answer includes "Memory recall: available"
    And the answer includes "Grounded explanations: available"
