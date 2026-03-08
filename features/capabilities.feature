@Rule:CapabilitiesHelp @Role:Resident @Priority:High @fast
Feature: Capabilities help responses
  In order to understand what the assistant can do
  As a resident
  I want help/capabilities prompts to return truthful runtime capability summaries

  @ISSUE-0013 @AC-0013-01
  Scenario Outline: HA unavailable with CLI fallback keeps text clarification available while satellite ask is unavailable
    Given a capabilities help prompt "<prompt>"
    When the stage answer flow handles capabilities under HA unavailable with CLI fallback
    Then the prompt is classified as capabilities help intent
    And the rendered answer should include semantic markers
      | marker                                  |
      | capability_satellite_actions_unavailable |
      | capability_cli_fallback_active          |
      | capability_clarification_available      |
      | capability_satellite_ask_unavailable    |
      | capability_debug_disabled               |

    Examples:
      | prompt          |
      | what can you do |
      | capabilities    |

  @ISSUE-0013 @AC-0013-02
  Scenario: HA available with satellite enabled returns available capability statements
    Given a capabilities help prompt "what can you do"
    When the stage answer flow handles capabilities under HA available with satellite enabled
    Then the prompt is classified as capabilities help intent
    And the rendered answer should include semantic markers
      | marker                                |
      | capability_satellite_actions_available |
      | capability_satellite_ask_available    |
      | capability_debug_enabled              |
      | capability_memory_recall_available    |
      | capability_grounded_explanations      |


  @ISSUE-0013 @AC-0013-03
  Scenario Outline: Direct satellite-action requests in CLI mode return capability alternatives
    Given a capabilities help prompt "<prompt>"
    When the stage answer flow handles capabilities under HA unavailable with CLI fallback
    Then the prompt is classified as capabilities help intent
    And the rendered answer should include semantic markers
      | marker                            |
      | capability_runtime_mode_cli       |
      | capability_satellite_action_label |
      | capability_action_alternatives    |

    Examples:
      | prompt                       |
      | ask via satellite            |
      | use satellite                |
      | start satellite conversation |
