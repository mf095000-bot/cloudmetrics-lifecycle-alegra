# Ejecuta la cadena Decision Agent -> Action Agent para un user_id real y
# muestra la salida de cada uno por separado, para verificar que el Action
# Agent consume EXCLUSIVAMENTE la salida del Decision Agent
# ({user_id, segment, segment_name, need, decision}), sin tocar HubSpot ni
# events.csv directamente.
#
# No ejecuta ninguna integración externa (no Resend, no Slack, no
# update_hubspot_contact).
#
# Uso: powershell -File scripts/run_action_agent.ps1 -UserId U00172

param(
    [Parameter(Mandatory = $true)]
    [string]$UserId
)

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $repoRoot "src\tools\hubspot_tool.ps1")
. (Join-Path $repoRoot "src\tools\events_tool.ps1")
. (Join-Path $repoRoot "src\agents\decision_agent.ps1")
. (Join-Path $repoRoot "src\agents\action_agent.ps1")

Write-Output "=== Decision Agent -> user_id=$UserId ==="
$decision = Invoke-DecisionAgent -UserId $UserId
$decision | Format-List

Write-Output "=== Action Agent (input = salida exacta del Decision Agent) ==="
$action = Invoke-ActionAgent -DecisionOutput $decision
$action | Format-List

Write-Output "=== JSON Action Agent ==="
$action | ConvertTo-Json
