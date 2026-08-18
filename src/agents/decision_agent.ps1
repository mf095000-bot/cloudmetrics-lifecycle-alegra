# Decision Agent (docs/07_AGENT_DESIGN.md §4)
#
# Responsabilidad: cruzar HubSpot (get_hubspot_contact) + eventos de producto
# (get_product_events) por user_id, reconstruir el estado del usuario y
# aplicar literalmente la tabla de docs/06_DECISION_LOGIC.md (que a su vez
# hereda los 5 segmentos de docs/05_SEGMENTATION.md) para producir:
# {user_id, segment, segment_name, need, decision}.
#
# No reinterpreta la segmentación ni la lógica de decisión, no crea
# segmentos/umbrales nuevos, no usa converted_to_paid ni atributos WHO
# (role, use_case, acquisition_channel, etc.) como entrada de la
# clasificación, no decide canal, no redacta mensajes, no ejecuta ninguna
# acción externa. Es de solo lectura.

$toolsDir = Join-Path (Split-Path -Parent $PSScriptRoot) "tools"
. (Join-Path $toolsDir "hubspot_tool.ps1")
. (Join-Path $toolsDir "events_tool.ps1")

$OnboardingFamily = @("onboarding_started", "profile_completed", "onboarding_completed")
$FirstValueFamily = @("data_source_connected", "dashboard_created", "insight_viewed")
$BehaviorFamily   = @("session_started", "dashboard_viewed", "feature_used", "dashboard_shared")

function Invoke-DecisionAgent {
    param(
        [Parameter(Mandatory = $true)]
        [string]$UserId
    )

    $contact = Get-HubSpotContact -UserId $UserId
    if (-not $contact) {
        throw "Decision Agent: no existe contacto en HubSpot para user_id=$UserId (docs/07_AGENT_DESIGN.md §4 requiere cruzar HubSpot + eventos por user_id)."
    }

    $events = Get-ProductEvents -UserId $UserId
    $eventNames = @($events | ForEach-Object { $_.event_name } | Select-Object -Unique)

    function Has([string]$Name) { return $eventNames -contains $Name }

    $segment = $null

    # Segmento 5 — docs/06_DECISION_LOGIC.md fila "Llegó a First Value"
    if ((Has "data_source_connected") -and (Has "dashboard_created") -and (Has "insight_viewed")) {
        $segment = [ordered]@{
            segment      = 5
            segment_name = "Llegó a First Value"
            need         = "No aplica dentro del alcance de Onboarding & Activation"
            decision     = "No existe una decisión de onboarding/activation pendiente para este segmento"
        }
    }
    # Segmento 4 — "Dashboard creado, sin insight"
    elseif ((Has "dashboard_created") -and -not (Has "insight_viewed")) {
        $segment = [ordered]@{
            segment      = 4
            segment_name = "Dashboard creado, sin insight"
            need         = "Encontrar o completar el paso final hacia un insight accionable"
            decision     = "Determinar que el usuario necesita completar el camino hacia First Value mediante la visualización del primer insight"
        }
    }
    # Segmento 3 — "Configurando, sin dashboard todavía"
    elseif (((Has "onboarding_completed") -or (Has "data_source_connected")) -and -not (Has "dashboard_created")) {
        $segment = [ordered]@{
            segment      = 3
            segment_name = "Configurando, sin dashboard todavía"
            need         = "Dar el salto de explorar el producto a construir su primer dashboard"
            decision     = "Determinar que el usuario necesita avanzar hacia la creación del primer dashboard"
        }
    }
    # Segmento 2 — "Estancado en onboarding"
    elseif ((Has "onboarding_started") -and -not (Has "onboarding_completed")) {
        $segment = [ordered]@{
            segment      = 2
            segment_name = "Estancado en onboarding"
            need         = "Completar la configuración inicial"
            decision     = "Determinar que el usuario necesita completar onboarding"
        }
    }
    # Segmento 1 — "Sin enganche real": registration_completed sin ningún evento
    # posterior de las familias Onboarding, First Value o Behavior.
    elseif ((Has "registration_completed") -and
            -not ($eventNames | Where-Object { ($OnboardingFamily + $FirstValueFamily + $BehaviorFamily) -contains $_ })) {
        $segment = [ordered]@{
            segment      = 1
            segment_name = "Sin enganche real"
            need         = "Un motivo para volver y empezar a usar el producto"
            decision     = "Determinar que el usuario necesita reenganche hacia el primer uso del producto"
        }
    }
    else {
        throw "Decision Agent: user_id=$UserId no encaja en ninguna fila de docs/06_DECISION_LOGIC.md con los eventos observados ($($eventNames -join ', ')). El Decision Agent opera post-registration_completed (docs/06_DECISION_LOGIC.md §1); no se inventa una regla nueva para este caso."
    }

    # Salida exacta definida en docs/07_AGENT_DESIGN.md §4 — ningún campo adicional.
    return [PSCustomObject]@{
        user_id      = $UserId
        segment      = $segment.segment
        segment_name = $segment.segment_name
        need         = $segment.need
        decision     = $segment.decision
    }
}
