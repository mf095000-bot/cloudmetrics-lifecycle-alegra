# Ejecuta el Decision Agent end-to-end para un user_id real y muestra la
# evidencia de cada paso (contacto real de HubSpot, eventos reales de
# events.csv, y la salida de decisión). No escribe nada en HubSpot ni en
# events.csv: get_hubspot_contact y get_product_events son de solo lectura.
#
# Uso: powershell -File scripts/run_decision_agent.ps1 -UserId U00172

param(
    [Parameter(Mandatory = $true)]
    [string]$UserId
)

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $repoRoot "src\tools\hubspot_tool.ps1")
. (Join-Path $repoRoot "src\tools\events_tool.ps1")
. (Join-Path $repoRoot "src\agents\decision_agent.ps1")

Write-Output "=== 1. user_id ==="
Write-Output $UserId

Write-Output "`n=== 2. Contacto real recuperado de HubSpot (get_hubspot_contact) ==="
$contact = Get-HubSpotContact -UserId $UserId
if (-not $contact) {
    throw "No se encontró contacto en HubSpot para user_id=$UserId"
}
$contact | Format-List

Write-Output "=== 3. Eventos reales recuperados de events.csv (get_product_events) ==="
$events = Get-ProductEvents -UserId $UserId
Write-Output "Total de eventos: $($events.Count)"
$events | Format-Table event_timestamp, event_name, anonymous_id, session_id -AutoSize

Write-Output "`n=== 4-7. Salida del Decision Agent ==="
$decision = Invoke-DecisionAgent -UserId $UserId
$decision | Format-List

Write-Output "=== JSON ==="
$decision | ConvertTo-Json
