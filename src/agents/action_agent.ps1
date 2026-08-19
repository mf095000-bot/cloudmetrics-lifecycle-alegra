# Action Agent (docs/07_AGENT_DESIGN.md §5, §6)
#
# Input: EXCLUSIVAMENTE la salida del Decision Agent
# {user_id, segment, segment_name, need, decision} — nunca datos crudos de
# HubSpot/Supabase (docs/07_AGENT_DESIGN.md §5 "Input").
#
# Responsabilidad de esta primera versión: determinar `action_type` a partir
# de `segment`, aplicando el mapping `decision -> action_type` ya aprobado
# por el usuario para esta fase (no definido en 06/07, aprobado fuera de
# esos documentos y registrado aquí explícitamente):
#
#   Segmentos 1-4 -> "user_email"
#   Segmento 5    -> "N/A" (no existe decisión de onboarding/activation
#                     pendiente para ese segmento)
#
# `internal_operational_action` (Slack) queda disponible arquitectónicamente
# (docs/07_AGENT_DESIGN.md §6, §9) pero no tiene condición de negocio activa
# en esta primera versión — no se inventa ninguna regla para dispararlo.
#
# Restricción explícita de esta fase: el Action Agent NO ejecuta ninguna
# acción externa todavía (no Resend, no Slack, no update_hubspot_contact, no
# Email/HTML Skill). Solo determina `action_type`. Por eso `executed` es
# siempre $false y no hay `resultado`/`sistema utilizado` reales — esos
# campos del contrato completo de docs/07_AGENT_DESIGN.md §5 se incorporan
# cuando se implemente la ejecución real.
#
# Límites (docs/07_AGENT_DESIGN.md §5 "Límites — no puede"): no cambia
# `decision` ni `need`, no vuelve a segmentar, no vuelve a diagnosticar, no
# inventa una necesidad distinta a la recibida, no decide por sí mismo
# cuándo escalar a Slack sin una condición de negocio ya definida.

$script:ActionTypeMap = @{
    1 = "user_email"
    2 = "user_email"
    3 = "user_email"
    4 = "user_email"
    5 = "N/A"
}

function Invoke-ActionAgent {
    param(
        [Parameter(Mandatory = $true)]
        [PSCustomObject]$DecisionOutput
    )

    $requiredFields = @("user_id", "segment", "segment_name", "need", "decision")
    foreach ($field in $requiredFields) {
        if (-not ($DecisionOutput.PSObject.Properties.Name -contains $field)) {
            throw "Action Agent: el objeto de entrada no tiene el campo requerido '$field'. El Action Agent solo puede recibir la salida exacta del Decision Agent (docs/07_AGENT_DESIGN.md §5)."
        }
    }

    $segment = [int]$DecisionOutput.segment
    if (-not $script:ActionTypeMap.ContainsKey($segment)) {
        throw "Action Agent: el segmento $segment no tiene un action_type aprobado en el mapping vigente. No se inventa un mapeo nuevo (docs/07_AGENT_DESIGN.md §4 límites)."
    }

    $actionType = $script:ActionTypeMap[$segment]

    $executionNote = switch ($actionType) {
        "user_email" { "action_type determinado; ejecucion real (Email/HTML Skill + send_email_resend) no implementada todavia en esta fase." }
        "N/A"        { "Segmento 5: no existe decision de onboarding/activation pendiente; no se determina ninguna accion ejecutable." }
        default      { "" }
    }

    return [PSCustomObject]@{
        user_id        = $DecisionOutput.user_id
        segment        = $DecisionOutput.segment
        segment_name   = $DecisionOutput.segment_name
        need           = $DecisionOutput.need
        decision       = $DecisionOutput.decision
        action_type    = $actionType
        executed       = $false
        execution_note = $executionNote
    }
}
