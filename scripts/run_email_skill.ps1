# Prueba la Email/HTML Skill encadenada al flujo real:
# Decision Agent -> Action Agent -> Email/HTML Skill.
#
# No envia ningun email, no llama a Resend/Slack/HubSpot-write. Las unicas
# llamadas externas de esta corrida son las de solo lectura del Decision
# Agent (get_hubspot_contact real, get_product_events sobre events.csv).
#
# Uso: powershell -File scripts/run_email_skill.ps1 -UserId U00172

param(
    [Parameter(Mandatory = $true)]
    [string]$UserId
)

$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $repoRoot "src\tools\hubspot_tool.ps1")
. (Join-Path $repoRoot "src\tools\events_tool.ps1")
. (Join-Path $repoRoot "src\agents\decision_agent.ps1")
. (Join-Path $repoRoot "src\agents\action_agent.ps1")
. (Join-Path $repoRoot "src\skills\email_html_skill.ps1")

Write-Output "=== Decision Agent -> user_id=$UserId ==="
$decision = Invoke-DecisionAgent -UserId $UserId
$decision | Format-List

Write-Output "=== Action Agent ==="
$action = Invoke-ActionAgent -DecisionOutput $decision
$action | Format-List

if ($action.action_type -ne "user_email") {
    Write-Output "action_type = $($action.action_type) -> la Email/HTML Skill no debe invocarse para este segmento. Deteniendo."
    exit 0
}

Write-Output "=== Email/HTML Skill (input = need + decision, nada mas) ==="
$email = Invoke-EmailHtmlSkill -Need $action.need -Decision $action.decision

Write-Output "--- subject ---"
Write-Output $email.subject

Write-Output "`n--- html ---"
Write-Output $email.html

Write-Output "`n--- text ---"
Write-Output $email.text

Write-Output "`n=== Validacion ==="

$checks = [ordered]@{}

$checks["subject no vacio"] = -not [string]::IsNullOrWhiteSpace($email.subject)
$checks["html no vacio"]    = -not [string]::IsNullOrWhiteSpace($email.html)
$checks["text no vacio"]    = -not [string]::IsNullOrWhiteSpace($email.text)

$checks["html contiene doctype"]     = $email.html -match "(?i)<!DOCTYPE html>"
$checks["html contiene <html>...</html> balanceado"] = (
    ([regex]::Matches($email.html, "(?i)<html").Count -eq [regex]::Matches($email.html, "(?i)</html>").Count) -and
    ([regex]::Matches($email.html, "(?i)<html").Count -ge 1)
)
$checks["html contiene <body>...</body> balanceado"] = (
    ([regex]::Matches($email.html, "(?i)<body").Count -eq [regex]::Matches($email.html, "(?i)</body>").Count) -and
    ([regex]::Matches($email.html, "(?i)<body").Count -ge 1)
)
$checks["html contiene <head>...</head> balanceado"] = (
    ([regex]::Matches($email.html, "(?i)<head").Count -eq [regex]::Matches($email.html, "(?i)</head>").Count) -and
    ([regex]::Matches($email.html, "(?i)<head").Count -ge 1)
)

$actionPhrase = $action.decision.Substring("Determinar que el usuario necesita ".Length).Trim()
$checks["subject contiene la frase de accion derivada de decision"] = $email.subject -like "*$actionPhrase*"
$checks["html contiene el need recibido"]  = $email.html -like "*$($action.need)*"
$checks["text contiene el need recibido"]  = $email.text -like "*$($action.need)*"
$checks["html contiene la frase de accion derivada de decision"] = $email.html -like "*$actionPhrase*"
$checks["text contiene la frase de accion derivada de decision"] = $email.text -like "*$actionPhrase*"

foreach ($k in $checks.Keys) {
    $status = if ($checks[$k]) { "OK" } else { "FALLA" }
    Write-Output "[$status] $k"
}

$allOk = -not ($checks.Values -contains $false)
Write-Output "`nResultado global: $(if ($allOk) { 'TODAS LAS VALIDACIONES PASARON' } else { 'HAY VALIDACIONES FALLIDAS' })"
