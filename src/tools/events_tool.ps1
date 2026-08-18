# Tool: get_product_events (docs/07_AGENT_DESIGN.md §7, §11 — docs/08A_INTEGRATION_SETUP.md §3)
#
# Fuente de eventos usada en esta primera demo (Fase 8B): data/events.csv,
# tratado como estand-in local de la tabla `events` de Supabase
# (docs/08A_INTEGRATION_SETUP.md §3.2). La fuente productiva prevista es
# Supabase. Cuando exista la conexión real, únicamente esta función debe
# cambiar (leer de Supabase en vez de events.csv); el Decision Agent y la
# lógica de negocio no deben modificarse, porque consumen exclusivamente el
# contrato de salida definido abajo.
#
# Contrato de salida por evento: event_id, event_timestamp, event_name,
# anonymous_id, session_id, metadata. `user_id` no se incluye en cada fila
# porque ya es el filtro de entrada de la función.

function Get-ProductEvents {
    param(
        [Parameter(Mandatory = $true)]
        [string]$UserId,

        [string]$EventsCsvPath
    )

    if (-not $EventsCsvPath) {
        $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
        $EventsCsvPath = Join-Path $repoRoot "data\events.csv"
    }

    if (-not (Test-Path $EventsCsvPath)) {
        throw "No se encontró events.csv en $EventsCsvPath"
    }

    $rows = Import-Csv -Path $EventsCsvPath |
        Where-Object { $_.user_id -eq $UserId }

    $sorted = $rows | Sort-Object {
        [datetime]::ParseExact($_.event_timestamp, "yyyy-MM-dd HH:mm:ss", $null)
    }

    return $sorted | ForEach-Object {
        $metadataObj = if ($_.metadata) { $_.metadata | ConvertFrom-Json } else { $null }
        [PSCustomObject]@{
            event_id        = $_.event_id
            event_timestamp = $_.event_timestamp
            event_name      = $_.event_name
            anonymous_id    = $_.anonymous_id
            session_id      = $_.session_id
            metadata        = $metadataObj
        }
    }
}
