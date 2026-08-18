# 08A_INTEGRATION_SETUP.md — Integration Setup (Fase 8A)

> Fuente de verdad de la Fase 8A — Automatizaciones / Integration Setup (`CLAUDE.md`, Fase 8). Especifica **qué** hay que conectar en HubSpot, Supabase, Resend y Slack para que la arquitectura ya cerrada en `docs/07_AGENT_DESIGN.md` pueda ejecutarse, y **qué estructura de datos/credenciales** requiere cada integración. No construye Decision Agent ni Action Agent, no define copy, no define timing ni el mapeo `decision → action_type` (eso queda para 08B en adelante). No reinterpreta `docs/04_DIAGNOSTIC_FINDINGS.md`, `docs/05_SEGMENTATION.md`, `docs/06_DECISION_LOGIC.md` ni `docs/07_AGENT_DESIGN.md`.

---

## 1. Punto de partida y límites de esta fase

Esta fase parte de `docs/07_AGENT_DESIGN.md` §18 ("Qué queda explícitamente para Fase 8"), del cual toma exactamente dos puntos:

> - Forma técnica del trigger (función, workflow, scheduler) y su implementación.
> - Automatización real y conexiones/API reales a HubSpot, Supabase, Resend y Slack.

**Esta fase (8A) resuelve únicamente el setup de esas conexiones**, no la automatización real. Explícitamente **no** hace en este documento:

- no construye Decision Agent ni Action Agent (eso es implementación, no setup);
- no define copy ni contenido de emails/Slack;
- no define timing, frecuencia, reintentos ni prioridad;
- no define el mapeo concreto `decision → action_type` (columna pendiente en `06_DECISION_LOGIC.md`/`07_AGENT_DESIGN.md` §5, §13, §18);
- no define la condición de negocio que dispara Slack (`07_AGENT_DESIGN.md` §9, §18);
- no modifica `docs/07_AGENT_DESIGN.md` ni ningún documento anterior: agentes, skills y tools ya definidos ahí se toman como dados;
- no genera datos nuevos ni reemplaza `data/users.csv` / `data/events.csv` (siguen congelados, `07_AGENT_DESIGN.md` §11).

Cada tool ya nombrada en `07_AGENT_DESIGN.md` §7 (`get_hubspot_contact`, `get_product_events`, `send_email_resend`, `send_slack_notification`, `update_hubspot_contact`) se especifica aquí en términos de: sistema real detrás de la tool, estructura de datos que debe existir para que la tool funcione, y credenciales/config requeridas. No se agregan tools nuevas.

---

## 2. HubSpot — Customer/Lifecycle Layer

### 2.1 Rol (heredado de `07_AGENT_DESIGN.md` §10, sin reinterpretar)

Fuente de identidad/estado del usuario y destino del registro de cada ciclo. Respalda `get_hubspot_contact` (lectura) y `update_hubspot_contact` (escritura).

### 2.2 Objeto HubSpot a usar

**Contact**, identificado por `email` (identificador nativo de HubSpot) — no por `user_id`. Se necesita un mapeo `user_id ↔ email` para poder cruzar con Supabase; ese mapeo ya existe en `data/users.csv` (`user_id`, `email`) y debe preservarse cuando `users.csv` deje de ser la fuente y HubSpot pase a serlo.

### 2.3 Custom properties requeridas en el objeto Contact

Ninguna de estas properties existe todavía en un HubSpot real; deben crearse antes de que `get_hubspot_contact`/`update_hubspot_contact` puedan operar.

| Property (internal name) | Tipo HubSpot | Origen del valor | Escrita por |
|---|---|---|---|
| `cm_user_id` | Single-line text | `users.csv.user_id` (o equivalente en producción) | Carga inicial / sistema de origen |
| `cm_signup_date` | Date | `users.csv.signup_date` | Carga inicial |
| `cm_country`, `cm_role`, `cm_industry`, `cm_company_size`, `cm_use_case`, `cm_acquisition_channel` | Text / dropdown según property | `users.csv` (atributos WHO) | Carga inicial |
| `cm_converted_to_paid` | Boolean | `users.csv.converted_to_paid` | Sistema de billing (fuera de este proyecto) |
| `cm_lifecycle_segment` | Number (1–5) o Text | Salida del Decision Agent (`segment`) | `update_hubspot_contact`, al cierre de cada ciclo |
| `cm_lifecycle_segment_name` | Single-line text | Salida del Decision Agent (`segment_name`) | `update_hubspot_contact` |
| `cm_lifecycle_decision` | Multi-line text | Salida del Decision Agent (`decision`) | `update_hubspot_contact` |
| `cm_last_action_type` | Text (`user_email` \| `internal_operational_action`) | Salida del Action Agent | `update_hubspot_contact` |
| `cm_last_action_result` | Text (`success` \| `error`) | Resultado de la ejecución | `update_hubspot_contact` |
| `cm_last_action_system` | Text (`resend` \| `slack`) | Sistema usado en el ciclo | `update_hubspot_contact` |
| `cm_last_action_timestamp` | Date/time | Timestamp del ciclo | `update_hubspot_contact` |
| `cm_last_action_error` | Multi-line text (nullable) | Mensaje de error, si existe | `update_hubspot_contact` |

Nota importante: `cm_lifecycle_segment` y las propiedades derivadas de él son **exactamente** las "variables derivadas" descritas en `CLAUDE.md` §6 — se calculan por el Decision Agent, nunca se cargan a mano ni se derivan dentro de HubSpot con workflows propios de HubSpot (eso sería reinterpretar la política de la Fase 6 fuera del Decision Agent, prohibido por `07_AGENT_DESIGN.md` §4/§16).

`cm_country`, `cm_role`, `cm_industry`, `cm_company_size`, `cm_use_case`, `cm_acquisition_channel` quedan disponibles en HubSpot solo como contexto secundario (`06_DECISION_LOGIC.md` §1); no deben ser leídos por el Decision Agent como entrada de la decisión (`07_AGENT_DESIGN.md` §4).

### 2.4 Qué debe poder leer `get_hubspot_contact(user_id)`

El objeto de contacto completo, o mínimamente: `cm_user_id`, `email`, `cm_signup_date`, `cm_lifecycle_segment` (estado previo), `cm_last_action_type`, `cm_last_action_result`, `cm_last_action_timestamp`. Las propiedades WHO pueden incluirse en la respuesta pero, por regla ya cerrada, el Decision Agent no las usa como entrada de clasificación.

### 2.5 Qué debe poder escribir `update_hubspot_contact(user_id, …)`

Exactamente los 7 campos listados en `07_AGENT_DESIGN.md` §10: segmento, decisión, `action_type`, acción ejecutada, sistema utilizado, timestamp, resultado (+ error si existe) → mapean 1:1 a las properties de la tabla anterior.

### 2.6 Credenciales y configuración

- **Private App token de HubSpot** (recomendado sobre OAuth de app pública para un caso interno) con scopes mínimos:
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.schemas.contacts.read` (para poder crear/verificar las custom properties)
- **Portal/Hub ID** de la cuenta HubSpot destino.
- Las 12 custom properties de §2.3 deben existir en el portal antes del primer ciclo (creación única, vía API de properties o UI de HubSpot).
- Variables de entorno sugeridas: `HUBSPOT_PRIVATE_APP_TOKEN`, `HUBSPOT_PORTAL_ID`.

---

## 3. Supabase — Product Behavioral Layer

### 3.1 Rol (heredado de `07_AGENT_DESIGN.md` §11, sin reinterpretar)

Fuente de eventos/comportamiento, con la misma taxonomía ya validada en `data/events.csv`. Solo lectura para el Decision Agent, vía `get_product_events`. `data/users.csv` y `data/events.csv` permanecen congelados; Supabase los sustituye conceptualmente como fuente conectada, no los reemplaza en este repo.

### 3.2 Estructura de datos requerida (mapeo directo desde el esquema ya validado del CSV)

**Tabla `events`** — mapea 1:1 las columnas ya presentes en `data/events.csv` (`event_id, event_timestamp, event_name, user_id, anonymous_id, session_id, metadata`):

| Columna | Tipo Postgres/Supabase | Notas |
|---|---|---|
| `event_id` | `text` PK | igual a `events.csv.event_id` |
| `event_timestamp` | `timestamptz` | igual a `events.csv.event_timestamp` |
| `event_name` | `text` | dominio cerrado, verificado sobre el dataset real: `registration_started`, `registration_completed`, `onboarding_started`, `profile_completed`, `onboarding_completed`, `data_source_connected`, `dashboard_created`, `insight_viewed`, `session_started`, `dashboard_viewed`, `feature_used`, `dashboard_shared` — exactamente los 12 valores usados por `06_DECISION_LOGIC.md` §3.1; ningún `event_name` nuevo debe introducirse sin pasar antes por Fase 4-6 |
| `user_id` | `text`, nullable | nulo en eventos pre-signup (`registration_started` sin cuenta creada aún, `CLAUDE.md` §5); se identifica por `anonymous_id` hasta que exista `user_id` |
| `anonymous_id` | `text` | identificador pre-signup, presente en el CSV real |
| `session_id` | `text` | |
| `metadata` | `jsonb` | estructura variable por `event_name`, ver §3.3 |

**Tabla `users`** — mapea 1:1 las columnas de `data/users.csv` (`user_id, first_name, last_name, email, country, signup_date, role, industry, company_size, use_case, acquisition_channel, converted_to_paid`). Esta tabla es la contraparte de "datos observados" (`CLAUDE.md` §6); ninguna variable derivada (`lifecycle_stage`, `first_action_timestamp`, `activation_status`, etc.) se almacena aquí — esas se calculan en el Decision Agent en tiempo de ejecución, nunca se persisten como columna de esta tabla.

### 3.3 `metadata` (jsonb) — formas observadas en el dataset real

Verificado directamente sobre `data/events.csv`; el Decision Agent no necesita interpretar `metadata` (la Fase 6 clasifica solo por presencia/ausencia de `event_name`), pero la tool debe devolverlo sin transformarlo:

| `event_name` | Forma de `metadata` |
|---|---|
| `data_source_connected` | `{"source_type": "..."}` (ej. `google_analytics`) |
| `dashboard_created` | `{"origin": "..."}` (ej. `from_scratch`) |
| `feature_used` | `{"feature": "..."}` |
| `insight_viewed` | `{"insight_type": "..."}` (ej. `trend`) |
| otros (`registration_started`, `registration_completed`, `onboarding_started`, `profile_completed`, `onboarding_completed`, `session_started`, `dashboard_viewed`, `dashboard_shared`) | `{}` en el dataset actual |

### 3.4 Qué debe poder leer `get_product_events(user_id)`

Todos los eventos de `events` para ese `user_id`, ordenados por `event_timestamp`, filtrando además por el `anonymous_id`/`session_id` previo al signup si se quiere reconstruir el abandono de registro (`CLAUDE.md` §5) — aunque esa reconstrucción de abandono de registro no es parte del alcance del Decision Agent de Fase 7 (que opera post-`registration_completed`, según `06_DECISION_LOGIC.md` Segmento 1).

### 3.5 Coherencia temporal exigida (heredada de `CLAUDE.md` §9, aplicable también a la fuente conectada)

Al migrar de CSV a Supabase, la validación de `scripts/validate_dataset.py` (eventos no preceden a `registration_started`; `registration_completed` no precede a `registration_started`) debe seguir cumpliéndose sobre la tabla `events` real — no se relaja por tratarse de una base de datos en vivo.

### 3.6 Credenciales y configuración

- **Supabase project URL** y **Service Role key** (lectura de backend, no anon key — el Decision Agent no corre en el navegador).
- Row Level Security: si se activa RLS sobre `events`/`users`, la Service Role key la bypassa por diseño; documentar explícitamente que el acceso es server-to-server, no de cliente.
- Variables de entorno sugeridas: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- Índices recomendados para que `get_product_events` sea eficiente: `events(user_id, event_timestamp)`, `events(anonymous_id)`.

---

## 4. Resend — infraestructura de envío de email

### 4.1 Rol (heredado de `07_AGENT_DESIGN.md` §12, sin reinterpretar)

Recibe `subject + html + text` ya producidos por el Email/HTML Skill dentro del Action Agent. Devuelve confirmación de envío o error. No decide ni segmenta.

### 4.2 Qué necesita recibir `send_email_resend`

Los tres campos que la Skill produce (`07_AGENT_DESIGN.md` §8): `subject`, `html`, `text`, más el destinatario. El destinatario es el `email` del contacto (HubSpot), no el `user_id` — Resend no conoce `user_id`.

Estructura mínima de la llamada (forma de datos, no implementación):

```
{
  "to": "<email del usuario, desde HubSpot>",
  "from": "<remitente verificado en Resend>",
  "subject": "<producido por Email/HTML Skill>",
  "html": "<producido por Email/HTML Skill>",
  "text": "<producido por Email/HTML Skill>"
}
```

### 4.3 Configuración de cuenta

- **Dominio de envío verificado** en Resend (registros DNS SPF/DKIM/DMARC) — sin esto Resend rechaza o degrada la entregabilidad; es un prerrequisito de infraestructura, no de código.
- **Dirección "from" verificada** sobre ese dominio.
- **API key** de Resend con permiso de envío.
- Variables de entorno sugeridas: `RESEND_API_KEY`, `RESEND_FROM_ADDRESS`.

### 4.4 Qué debe devolver `send_email_resend` para que el Action Agent pueda registrar resultado

Confirmación de envío (id de mensaje) o error explícito — este resultado es lo que se escribe luego en `cm_last_action_result` / `cm_last_action_error` de HubSpot (§2.3).

---

## 5. Slack — comunicación operativa interna

### 5.1 Rol (heredado de `07_AGENT_DESIGN.md` §9, sin reinterpretar)

Tool de comunicación **interna** (equipo), no con el usuario final. Entrega el mensaje que el Action Agent ya determinó enviar; no decide a quién ni cuándo escalar — esa condición de negocio queda fuera del alcance de esta fase (`07_AGENT_DESIGN.md` §18).

### 5.2 Qué necesita recibir `send_slack_notification`

Contexto estructurado ya construido por el Action Agent (`07_AGENT_DESIGN.md` §9): `user_id`, segmento, necesidad, decisión, motivo. Forma mínima de datos:

```
{
  "channel": "<canal Slack de destino, a definir en 08B>",
  "context": {
    "user_id": "...",
    "segment": 1,
    "segment_name": "...",
    "need": "...",
    "decision": "...",
    "reason": "..."
  }
}
```

El canal de destino concreto (ej. `#lifecycle-alerts`) y la condición de negocio que dispara el envío no se definen en 8A — son parte del mapeo `decision → action_type` pendiente (`07_AGENT_DESIGN.md` §13, §18).

### 5.3 Configuración de cuenta

- **Slack App** instalada en el workspace del equipo, con scope `chat:write` (bot token) — suficiente para publicar en canales donde el bot fue invitado; no requiere scopes de lectura de usuario.
- **Bot token** (`xoxb-...`) y **canal(es) de destino** ya creados en el workspace (ej. Product/CS).
- Alternativa más simple si no se requiere un bot persistente: **Incoming Webhook** por canal — evaluar en 08B según si se necesita un solo canal fijo o enrutamiento dinámico por segmento/equipo.
- Variables de entorno sugeridas: `SLACK_BOT_TOKEN` (o `SLACK_WEBHOOK_URL` si se usa webhook) y el/los `SLACK_CHANNEL_ID` de destino.

---

## 6. Resumen de credenciales/config a aprovisionar

| Sistema | Credencial | Scope/permiso mínimo |
|---|---|---|
| HubSpot | Private App token + Portal ID | `crm.objects.contacts.read/write`, `crm.schemas.contacts.read` |
| Supabase | Project URL + Service Role key | lectura server-side sobre `events`, `users` |
| Resend | API key + dominio/from verificado | envío de email transaccional |
| Slack | Bot token (`chat:write`) o Webhook URL + canal | publicación en canal interno |

Ninguna de estas credenciales se versiona en el repositorio; quedan como variables de entorno a definir en el entorno de ejecución cuando 8B implemente las conexiones reales.

---

## 7. Qué queda explícitamente para después de 8A

- Implementación real de las 5 tools (`get_hubspot_contact`, `get_product_events`, `send_email_resend`, `send_slack_notification`, `update_hubspot_contact`) contra las APIs reales.
- Construcción del Decision Agent y del Action Agent descritos en `07_AGENT_DESIGN.md`.
- Mapeo concreto `decision → action_type` y condición de negocio para Slack.
- Copy/contenido de emails y notificaciones.
- Canal(es) Slack concretos y su enrutamiento por segmento/equipo.
- Timing, frecuencia, reintentos, forma técnica del trigger (función/workflow/scheduler).
- Carga inicial real de las 12 custom properties en un portal HubSpot y de las tablas `users`/`events` en un proyecto Supabase reales (hoy son especificación, no artefactos provisionados).

Este documento entrega la especificación de conexión; no las conexiones en sí.
