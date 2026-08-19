# Runner de demo: Decision Agent -> Action Agent, extremo a extremo.
#
# Uso:
#   ./scripts/run_action_agent.ps1 -UserId U00172
#
# Requiere las mismas variables de entorno que scripts/run_decision_agent.ps1
# (credenciales de HubSpot -- ver .env.example).

param(
    [Parameter(Mandatory = $true)]
    [string]$UserId
)

$agentsDir = Join-Path $PSScriptRoot "../src/agents"
. (Join-Path $agentsDir "decision_agent.ps1")
. (Join-Path $agentsDir "action_agent.ps1")

$decision = Invoke-DecisionAgent -UserId $UserId
Write-Host "--- Decision Agent ---"
$decision | Format-List

$action = Invoke-ActionAgent -Decision $decision
Write-Host "--- Action Agent ---"
$action | Format-List
