# Email/HTML Skill (docs/07_AGENT_DESIGN.md §8)
#
# Vive conceptualmente dentro del Action Agent; no es un agente independiente
# y no llama a ningun sistema externo. Se invoca unicamente cuando
# action_type = user_email (decidido por el Action Agent, no por esta Skill).
#
# Input: unicamente {need, decision} — el objeto de decision del Decision
# Agent, ya filtrado por el Action Agent. Esta Skill no recibe ni consulta
# user_id, email, ni ningun dato crudo de HubSpot/events.csv.
#
# Output: {subject, html, text}. No envia nada — el envio lo hace Resend via
# send_email_resend (no implementado todavia).
#
# Regla que debe respetar (docs/07_AGENT_DESIGN.md §8): el contenido debe ser
# trazable a la decision/need recibida; no puede introducir una necesidad,
# urgencia o promesa ajena a la decision de Fase 6. Por eso el contenido se
# construye unicamente a partir de $Need y $Decision — no se agrega nombre
# de usuario, empresa, ni ninguna otra informacion no presente en el input.
#
# El CTA usa href="#" deliberadamente: esta Skill no conoce la URL real del
# producto (no forma parte de su input), asi que no se inventa un destino.
# Resolver la URL real del CTA es trabajo de una fase posterior (Action
# Agent/config), no de esta Skill.

function Invoke-EmailHtmlSkill {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Need,

        [Parameter(Mandatory = $true)]
        [string]$Decision
    )

    $actionPrefix = "Determinar que el usuario necesita "
    if ($Decision -notlike "$actionPrefix*") {
        throw "Email/HTML Skill: la decision recibida ('$Decision') no tiene la forma de una decision accionable de onboarding/activation. Esta Skill solo debe invocarse cuando action_type = user_email (docs/07_AGENT_DESIGN.md §8)."
    }

    $actionPhrase = $Decision.Substring($actionPrefix.Length).Trim()
    $actionPhraseCap = $actionPhrase.Substring(0, 1).ToUpper() + $actionPhrase.Substring(1)

    $subject = "CloudMetrics: $actionPhraseCap"

    $html = @"
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>$subject</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f5f7; font-family: Arial, Helvetica, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7; padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px; width:100%; background-color:#ffffff; border-radius:8px; overflow:hidden;">
          <tr>
            <td style="background-color:#1a1a2e; padding:20px 24px;">
              <span style="color:#ffffff; font-size:18px; font-weight:bold; letter-spacing:0.5px;">CloudMetrics</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 24px 8px 24px;">
              <p style="margin:0 0 16px 0; font-size:15px; line-height:22px; color:#1a1a2e;">Hola,</p>
              <p style="margin:0 0 16px 0; font-size:15px; line-height:22px; color:#1a1a2e;">Tu próximo paso en CloudMetrics: <strong>$Need</strong>.</p>
              <p style="margin:0 0 24px 0; font-size:15px; line-height:22px; color:#1a1a2e;">$actionPhraseCap.</p>
            </td>
          </tr>
          <tr>
            <td align="left" style="padding:0 24px 32px 24px;">
              <a href="#" style="display:inline-block; background-color:#2f6fed; color:#ffffff; text-decoration:none; font-size:14px; font-weight:bold; padding:12px 20px; border-radius:6px;">$actionPhraseCap</a>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 24px 24px 24px; border-top:1px solid #eaeaea;">
              <p style="margin:0; font-size:12px; line-height:18px; color:#6b7280;">Este correo es parte del seguimiento de tu cuenta en CloudMetrics.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"@

    $text = @"
Hola,

Tu próximo paso en CloudMetrics: $Need.

$actionPhraseCap.

-> $actionPhraseCap

Este correo es parte del seguimiento de tu cuenta en CloudMetrics.
"@

    return [PSCustomObject]@{
        subject = $subject
        html    = $html
        text    = $text
    }
}
