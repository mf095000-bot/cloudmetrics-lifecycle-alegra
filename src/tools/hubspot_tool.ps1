# Tool: get_hubspot_contact (docs/07_AGENT_DESIGN.md §7, §10 — docs/08A_INTEGRATION_SETUP.md §2)
#
# Conexión real de solo lectura al Customer/Lifecycle Layer (HubSpot).
# Busca el Contact por la custom property `user_id` (no por email) porque
# `user_id` es el identificador común que permite cruzar HubSpot con la capa
# de comportamiento (events.csv hoy, Supabase después).
#
# Solo se leen las properties que existen realmente hoy en el portal.
# No se leen ni se inventan properties `cm_*` adicionales a `cm_lifecycle_segment`,
# y esa property no se escribe desde esta tool (es de solo lectura).

function Get-HubSpotContact {
    param(
        [Parameter(Mandatory = $true)]
        [string]$UserId
    )

    $token = $env:HUBSPOT_PRIVATE_APP_TOKEN
    if (-not $token) {
        throw "HUBSPOT_PRIVATE_APP_TOKEN no está configurado en el entorno."
    }

    $headers = @{
        Authorization  = "Bearer $token"
        "Content-Type" = "application/json"
    }

    $properties = @(
        "user_id", "email", "firstname", "lastname",
        "signup_date", "role", "use_case",
        "acquisition_channel", "converted_to_paid"
    )

    $body = @{
        filterGroups = @(
            @{
                filters = @(
                    @{ propertyName = "user_id"; operator = "EQ"; value = $UserId }
                )
            }
        )
        properties = $properties
        limit      = 1
    } | ConvertTo-Json -Depth 6

    $response = Invoke-RestMethod `
        -Uri "https://api.hubapi.com/crm/v3/objects/contacts/search" `
        -Headers $headers -Method Post -Body $body

    if (-not $response.results -or $response.results.Count -eq 0) {
        return $null
    }

    $contact = $response.results[0]

    return [PSCustomObject]@{
        hubspot_id          = $contact.id
        user_id             = $contact.properties.user_id
        email               = $contact.properties.email
        firstname           = $contact.properties.firstname
        lastname            = $contact.properties.lastname
        signup_date         = $contact.properties.signup_date
        role                = $contact.properties.role
        use_case            = $contact.properties.use_case
        acquisition_channel = $contact.properties.acquisition_channel
        converted_to_paid   = $contact.properties.converted_to_paid
    }
}
