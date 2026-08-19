# Action Agent (docs/07_AGENT_DESIGN.md §5)
#
# Responsabilidad: convertir la decisión ya validada del Decision Agent en un
# action_type ejecutable. Consume exclusivamente el output del Decision Agent
# ({user_id, segment, segment_name, need, decision}) -- nunca datos crudos de
# HubSpot/Supabase. No decide de negocio: no cambia la decision ni la need
# recibidas, no vuelve a segmentar, no vuelve a diagnosticar.
#
# Mapeo decision -> action_type (docs/07_AGENT_DESIGN.md §6, §13, §18):
#   segmento 1-4 -> "user_email"   (hay una decision de onboarding/activation
#                                   pendiente, se comunica al usuario final)
#   segmento 5   -> "N/A"          (docs/06_DECISION_LOGIC.md: "no existe una
#                                   decision de onboarding/activation
#                                   pendiente para este segmento")
#
# "internal_operational_action" (Slack) queda definido en el contrato de
# docs/07_AGENT_DESIGN.md §6 pero esta version no lo dispara: la condicion de
# negocio que lo activaria no esta definida en ningun documento cerrado
# (docs/07_AGENT_DESIGN.md §9, §18) y no se inventa aqui.
#
# Esta version NO ejecuta ninguna llamada externa real (no send_email_resend,
# no send_slack_notification, no update_hubspot_contact). executed queda
# siempre en $false y execution_note documenta por que -- es una
# implementacion parcial intencional de este checkpoint (Fase 8A: MVP/demo),
# no una desviacion del diseno de docs/07_AGENT_DESIGN.md.

function Invoke-ActionAgent {
    param(
        [Parameter(Mandatory = $true)]
        [PSCustomObject]$Decision
    )

    foreach ($field in @('user_id', 'segment', 'segment_name', 'need', 'decision')) {
        if (-not (Get-Member -InputObject $Decision -Name $field -MemberType NoteProperty)) {
            throw "Action Agent: el objeto recibido no es una salida valida del Decision Agent (falta el campo '$field'). El Action Agent solo consume {user_id, segment, segment_name, need, decision} -- docs/07_AGENT_DESIGN.md §5."
        }
    }

    $actionType = $null
    if ($Decision.segment -ge 1 -and $Decision.segment -le 4) {
        $actionType = "user_email"
    }
    elseif ($Decision.segment -eq 5) {
        $actionType = "N/A"
    }
    else {
        throw "Action Agent: segmento '$($Decision.segment)' no reconocido. Solo existen los 5 segmentos de docs/05_SEGMENTATION.md; el Action Agent no crea segmentos nuevos."
    }

    $executed = $false
    $executionNote = if ($actionType -eq "N/A") {
        "No aplica -- no existe decision de onboarding/activation pendiente para este segmento (docs/06_DECISION_LOGIC.md, fila Segmento 5)."
    } else {
        "action_type determinado ($actionType); envio real no implementado en este checkpoint -- Email/HTML Skill y send_email_resend quedan para cuando existan credenciales de Resend (docs/08A_INTEGRATION_SETUP.md §4, §7)."
    }

    # Salida: extiende el objeto de decision con action_type + resultado de
    # ejecucion. No modifica user_id/segment/segment_name/need/decision.
    return [PSCustomObject]@{
        user_id        = $Decision.user_id
        segment        = $Decision.segment
        segment_name   = $Decision.segment_name
        need           = $Decision.need
        decision       = $Decision.decision
        action_type    = $actionType
        executed       = $executed
        execution_note = $executionNote
    }
}
