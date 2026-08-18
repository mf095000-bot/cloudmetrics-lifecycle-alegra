# 07_AGENT_DESIGN.md — Arquitectura de agentes (Fase 7)

> Fuente de verdad de la Fase 7 — Agentes (`CLAUDE.md`, Fase 7). Operacionaliza la política ya cerrada en `docs/06_DECISION_LOGIC.md` (que a su vez se apoya en `docs/05_SEGMENTATION.md` y `docs/04_DIAGNOSTIC_FINDINGS.md`) en una arquitectura de sistema capaz de ejecutarse sin intervención manual. No reabre diagnóstico, segmentación ni política de decisión. No define copy, canales concretos por segmento, timing, ni conexiones técnicas reales — eso corresponde a la Fase 8.

---

## 1. Punto de partida

Esta fase parte de tres documentos ya cerrados y no los reinterpreta:

- `docs/04_DIAGNOSTIC_FINDINGS.md`: el comportamiento (WHAT) es la señal dominante; no hay un único bottleneck.
- `docs/05_SEGMENTATION.md`: los 5 segmentos, definidos por dónde se detiene cada usuario en el funnel observable.
- `docs/06_DECISION_LOGIC.md`: la tabla de decisión que traduce cada segmento en necesidad, decisión, condición de salida y resultado de éxito.

**Regla de esta fase:** el conocimiento construido manualmente en las Fases 4–6 no se descubre de nuevo — se convierte en una capacidad operacional automatizada. Ningún componente descrito aquí puede reinterpretar, extender o crear reglas de negocio, segmentos, subsegmentos, umbrales o criterios estadísticos nuevos.

---

## 2. Arquitectura general

```
        ┌───────────────┐                    ┌───────────────┐
        │   HUBSPOT     │                    │   SUPABASE    │
        │  Customer/    │                    │  Product      │
        │  Lifecycle    │                    │  Behavioral   │
        │  Layer        │                    │  Layer        │
        └───────┬───────┘                    └───────┬───────┘
                │ contacto/estado                     │ eventos/comportamiento
                └───────────────┬──────────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │  DECISION AGENT │
                        │  estado→segmento │
                        │  →necesidad→     │
                        │  decisión         │
                        │  (Fase 5+6, sin   │
                        │  reinterpretar)   │
                        └────────┬────────┘
                                 │ decisión validada
                                 ▼
                        ┌─────────────────┐
                        │  ACTION AGENT   │
                        │  decisión →      │
                        │  action_type     │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              user_email            internal_operational_action
                    │                         │
          Email/HTML Skill           send_slack_notification
                    │                         │
          send_email_resend                   │
                    ▼                         ▼
                 RESEND                  equipo interno
                    │                         │
                    └────────────┬────────────┘
                                 ▼
                        registrar resultado
                                 ▼
                    update_hubspot_contact (estado)
                                 ▼
                            nuevo ciclo
```

No hay orquestador externo (no n8n, no otra plataforma de workflows). La coordinación del flujo es responsabilidad de la cadena Decision Agent → Action Agent, invocada por un trigger cuya forma técnica (función, workflow, scheduler) es implementación y queda para Fase 8. Claude Code es el entorno donde esta arquitectura se construirá, no un componente de negocio de la arquitectura misma.

---

## 3. Separación estricta de responsabilidades

| Tipo de componente | Rol | Ejemplos |
|---|---|---|
| Agente | Tiene una responsabilidad de negocio distinta y propia | Decision Agent (decide), Action Agent (ejecuta) |
| Skill | Capacidad especializada y reutilizable, interna a un agente, sin conexión directa a sistemas externos | Email/HTML Skill |
| Tool | Conexión con un sistema externo | `get_hubspot_contact`, `get_product_events`, `send_email_resend`, `send_slack_notification`, `update_hubspot_contact` |

Regla: **Decision Agent = decide. Action Agent = ejecuta.** Ningún otro componente decide ni ejecuta lógica de negocio.

---

## 4. Decision Agent

- **Propósito**: cruzar HubSpot + Supabase por `user_id`, reconstruir el estado del usuario, determinar su segmento (Fase 5) y su decisión de lifecycle (Fase 6).
- **Inputs**: contacto/atributos/estado (HubSpot, vía `get_hubspot_contact`) + eventos/comportamiento (Supabase, vía `get_product_events`).
- **Outputs**: objeto de decisión validada:
  ```
  {
    "user_id": "...",
    "segment": 3,
    "segment_name": "Configurando, sin dashboard todavía",
    "need": "Dar el salto de explorar el producto a construir su primer dashboard",
    "decision": "Orientar al usuario hacia la creación de su primer dashboard"
  }
  ```
- **Cómo cruza las fuentes**: usa `user_id` como identificador común entre HubSpot (identidad/estado) y Supabase (comportamiento) para construir un único estado consolidado antes de clasificar.
- **Cómo clasifica el segmento**: aplica literalmente la columna "Estado observable / Señal de entrada" de `06_DECISION_LOGIC.md` sobre el estado reconstruido — sin inferencia estadística, sin clustering, sin modelo.
- **Cómo evita intervenir sobre un usuario que ya avanzó de segmento**: la condición de salida de cada fila de `06_DECISION_LOGIC.md` es un evento observable; si ese evento ya está presente en el estado reconstruido, el usuario no pertenece más a ese segmento y se reclasifica según su estado actual.
- **Tools**: `get_hubspot_contact`, `get_product_events` (ambas de solo lectura).
- **Límites — no puede**:
  - reinterpretar `05_SEGMENTATION.md` ni `06_DECISION_LOGIC.md`;
  - crear segmentos, subsegmentos o umbrales nuevos;
  - usar `converted_to_paid` como criterio;
  - usar atributos WHO (`country`, `role`, `industry`, `acquisition_channel`, `company_size`, `use_case`) como entrada de la decisión;
  - decidir canal;
  - redactar mensajes;
  - ejecutar ninguna acción externa;
  - determinar `action_type` — eso es exclusivo del Action Agent.

---

## 5. Action Agent

- **Propósito**: convertir una decisión de lifecycle ya validada en una acción ejecutable, y ejecutarla.
- **Input**: exclusivamente el objeto de salida del Decision Agent (`segment`, `segment_name`, `need`, `decision`) — nunca datos crudos de HubSpot/Supabase.
- **Cómo determina `action_type`**: mapea conceptualmente la `decision` recibida a uno de los dos tipos de acción soportados (sección 6). El mapeo concreto — qué filas de `06_DECISION_LOGIC.md` producen cada `action_type` — no se define en esta fase (ver sección 13).
- **Output**: acción ejecutada + resultado (éxito/error) + `action_type` + sistema utilizado.
- **Tools**: `send_email_resend`, `send_slack_notification`, `update_hubspot_contact`.
- **Skill**: Email/HTML Skill, invocada únicamente cuando `action_type = user_email`.
- **Límites — no puede**:
  - cambiar la `decision` ni la `need` recibidas;
  - volver a segmentar;
  - volver a diagnosticar;
  - inventar una necesidad distinta a la recibida;
  - decidir por sí mismo cuándo escalar a Slack sin una condición de negocio ya definida (ver sección 8).

---

## 6. Dos tipos de acción

| `action_type` | Destino | Skill/Tool usada |
|---|---|---|
| `user_email` | Usuario final | Email/HTML Skill → `send_email_resend` |
| `internal_operational_action` | Equipo interno (Product, Customer Success, etc.) | `send_slack_notification` |

Ambos tipos parten del mismo objeto de decisión del Decision Agent; la bifurcación ocurre exclusivamente dentro del Action Agent. Otros canales quedan como extensión futura, no incorporados en esta fase.

---

## 7. Tools

| Agente | Tools |
|---|---|
| Decision Agent | `get_hubspot_contact`, `get_product_events` |
| Action Agent | `send_email_resend`, `send_slack_notification`, `update_hubspot_contact` |

Cada tool existe porque conecta con un sistema externo distinto (HubSpot, Supabase, Resend, Slack). Ninguna tool decide ni interpreta — solo lee o escribe contra su sistema.

---

## 8. Email/HTML Skill

- Vive dentro del Action Agent; no es un agente independiente.
- Se invoca únicamente cuando `action_type = user_email`.
- **Recibe**: el objeto de decisión (`need`, `decision`) desde el Action Agent.
- **Produce**: `subject + html + plain text`.
- **No envía** — el envío lo realiza Resend vía `send_email_resend`.
- **Regla que debe respetar**: el contenido debe ser trazable a la `decision`/`need` recibida; no puede introducir una necesidad, urgencia o promesa ajena a la decisión de Fase 6.
- **Quién puede invocarlo**: únicamente el Action Agent.

---

## 9. Slack

- Es una **tool**, no un agente.
- Sirve para comunicación operativa **interna** (equipo), no para comunicación con el usuario final.
- Se invoca vía `send_slack_notification` cuando `action_type = internal_operational_action`, con contexto estructurado (`user_id`, segmento, necesidad, decisión, motivo) ya construido por el Action Agent.
- **No decide** cuándo ni a quién escalar — solo entrega el mensaje que el Action Agent ya determinó enviar.
- La condición de negocio concreta que dispara un escalamiento a Slack (qué segmento, qué situación) **no está definida en Fase 6** y no se inventa aquí; queda como capacidad arquitectónica disponible para que Fase 8 la active con una regla explícita.

---

## 10. HubSpot

- **Rol**: Customer/Lifecycle Layer — fuente de identidad y estado, y destino del registro de cada ciclo.
- **Lee** (vía `get_hubspot_contact`): identidad/contacto, atributos de usuario, información de cuenta, estado de lifecycle previo.
- **Escribe** (vía `update_hubspot_contact`), al cierre de cada ciclo, conceptualmente:
  - segmento;
  - decisión;
  - `action_type`;
  - acción ejecutada;
  - sistema utilizado;
  - timestamp;
  - resultado;
  - error, si existe.
- No decide, no ejecuta. No es el proveedor de envío de email (ese rol es de Resend).

## 11. Supabase

- **Rol**: Product Behavioral Layer — fuente de eventos y comportamiento (misma taxonomía ya validada en `events.csv`, ahora como fuente conectada en lugar de archivo congelado).
- Solo lectura para el Decision Agent (vía `get_product_events`). No decide, no ejecuta.
- Los CSV (`data/users.csv`, `data/events.csv`) permanecen congelados como base histórica de las Fases 4–6 y no son modificados ni reemplazados en esta fase; la arquitectura solo documenta que Supabase podrá sustituirlos conceptualmente más adelante.

## 12. Resend

- Infraestructura de envío de email. Recibe `subject + html + text` ya producidos por el Email/HTML Skill. Devuelve confirmación de envío o error.
- No segmenta, no decide, no genera estrategia, no orquesta.

---

## 13. Flujo end-to-end

```
Trigger
  → obtener user_id
  → get_hubspot_contact(user_id)
  → get_product_events(user_id)
  → Decision Agent: cruce → estado → segmento → necesidad → decisión
  → validar decisión
  → Action Agent: decisión → action_type
       si action_type = user_email:
           → Email/HTML Skill → send_email_resend(...)
       si action_type = internal_operational_action:
           → send_slack_notification(...)
  → registrar resultado
  → update_hubspot_contact(segmento, decisión, action_type, acción, sistema, timestamp, resultado, error)
```

## 14. Lifecycle Loop

```
1.  Usuario existe en HubSpot
2.  Usuario tiene comportamiento en Supabase
3.  Sistema cruza ambas fuentes por user_id
4.  Decision Agent reconstruye el estado
5.  Decision Agent determina segmento
6.  Decision Agent determina necesidad
7.  Decision Agent aplica la política (06_DECISION_LOGIC.md)
8.  Action Agent recibe la decisión validada
9.  Action Agent determina action_type
10. Si user_email: Email/HTML Skill genera el contenido
11. Resend ejecuta el envío (o Slack notifica al equipo interno)
12. Resultado se registra
13. HubSpot se actualiza (segmento, decisión, action_type, resultado)
14. Usuario continúa interactuando con el producto
15. Nuevos eventos llegan a Supabase
16. El ciclo puede volver a ejecutarse
```

Esto es un **loop**, no una ejecución aislada: la actualización de HubSpot al final de un ciclo alimenta la próxima lectura del Decision Agent, incluida la detección de que un usuario ya cumplió la condición de salida de su decisión anterior.

---

## 15. Matriz de responsabilidades

| Componente | Decide | Lee | Produce | Ejecuta |
|---|---|---|---|---|
| Trigger/coordinación (Decision Agent → Action Agent) | Cuándo se invoca cada agente | — | Secuencia de la corrida | Dispara el ciclo, no la lógica de negocio |
| HubSpot | — | Contacto, atributos, estado previo | — | Persiste estado actualizado |
| Supabase | — | Eventos/comportamiento | — | Persiste eventos nuevos |
| Decision Agent | Segmento, necesidad, decisión | HubSpot + Supabase (vía tools) | `{segment, need, decision}` | — |
| Action Agent | `action_type` | Output del Decision Agent | Acción + resultado | Invoca Skill y tools |
| Email/HTML Skill | — | Decisión recibida | subject + html + text | — |
| Resend | — | Email listo | Confirmación/error | Envía el email |
| Slack | — | Contexto estructurado del Action Agent | Confirmación/error | Notifica al equipo interno |

## 16. Límites de cada componente

| Componente | No puede |
|---|---|
| Decision Agent | decidir canal, redactar mensajes, ejecutar acciones, definir `action_type` |
| Action Agent | cambiar decisión/necesidad, re-segmentar, diagnosticar, inventar cuándo escalar a Slack |
| Email/HTML Skill | enviar el email, ser invocado por otro que no sea el Action Agent |
| Resend | decidir, segmentar, orquestar |
| Slack | decidir a quién/cuándo escalar; solo entrega lo que el Action Agent le pasa |
| HubSpot / Supabase | decidir o ejecutar — son fuentes/destinos, no lógica |

---

## 17. Relación con Fases 4–6

```
FASES 4–6: Diagnóstico → Segmentación → Decision Logic   (conocimiento, cerrado)
                              ↓ operacionalización ↓
FASE 7: Fuentes conectadas (HubSpot+Supabase) → Decision Agent → Action Agent → Skill/Tools → sistemas externos (Resend/Slack)
                              ↓ ejecución ↓
FASE 8: Lifecycle real (mapeo decision→action_type, condiciones de Slack, copy, canales, timing, automatizaciones)
```

El Decision Agent no descubre diagnóstico ni segmentación de nuevo — ejecuta lo ya cerrado en `docs/04_DIAGNOSTIC_FINDINGS.md`, `docs/05_SEGMENTATION.md` y `docs/06_DECISION_LOGIC.md`.

---

## 18. Qué queda explícitamente para Fase 8

- Mapeo concreto `decision → action_type` (qué filas de `06_DECISION_LOGIC.md` producen `user_email` vs. `internal_operational_action`).
- Condiciones de negocio concretas para disparar Slack (qué segmento, qué situación).
- Copy y contenido concreto de emails y notificaciones internas.
- Canales adicionales a email/Slack.
- Timing de intervención, frecuencia, reintentos, prioridad temporal.
- Journeys multi-paso.
- Forma técnica del trigger (función, workflow, scheduler) y su implementación.
- Automatización real y conexiones/API reales a HubSpot, Supabase, Resend y Slack.

Esta arquitectura está diseñada para demostrar capacidad de integración real entre múltiples sistemas (CRM, base de comportamiento, envío de email, comunicación operativa interna); la implementación de esas conexiones se realiza en una etapa posterior, no en esta fase.
