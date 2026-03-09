@Rule:StartupStatus @Role:Ops @Priority:High @fast
Feature: Startup degraded-mode messaging
  In order to trust degraded startup behavior
  As an operations stakeholder
  I want startup status output to explicitly document CLI fallback and continuity messaging

  @ISSUE-0016 @AC-0016-01
  Scenario: HA unavailable startup in auto mode reports explicit CLI fallback and continuity messaging
    Given startup mode "auto" with daemon set to "false"
    And Home Assistant connection is unavailable during startup checks
    And Ollama connection is available during startup checks
    When startup status is rendered
    Then startup output should include "Selected mode: cli (requested=auto, fallback reason=satellite connection is unavailable, daemon=False)"
    And startup output should include "Developer note: satellite interface disabled; CLI fallback will be used unless --daemon is set."
    And startup output should include "Continuity: memory cards are shared across interfaces in-process via one vector store."

