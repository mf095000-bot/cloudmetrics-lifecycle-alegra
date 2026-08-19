# 08C_PERSONALIZATION.md — Personalización por contexto WHO (Fase 8C)

> Fuente de verdad de la Fase 8C — Personalización (`CLAUDE.md`, Fase 8, continuación de `docs/08A_INTEGRATION_SETUP.md` y `docs/08B_TRIGGER_AND_LEARNING.md`). Responde una pregunta que surgió al revisar la arquitectura: ¿hace falta un agente de personalización por `use_case` (u otro atributo WHO)? Este documento cierra esa pregunta y especifica dónde vive la personalización, con qué límites. No crea un agente nuevo, no reabre diagnóstico, segmentación ni la política de decisión, y no modifica `docs/07_AGENT_DESIGN.md` — lo extiende.

---

## 1. Punto de partida

Esta fase parte de cuatro documentos ya cerrados y no los reinterpreta:

- `docs/04_DIAGNOSTIC_FINDINGS.md` §4: `use_case` mostró señal **débil y marginal** sobre conversión; no se consideró prioritaria para segmentación. `country`, `role` y `acquisition_channel` mostraron señal más robusta, pero tampoco definieron ningún segmento.
- `docs/05_SEGMENTATION.md` §4: los atributos WHO (`country`, `role`, `acquisition_channel`, `company_size`, `industry`, `use_case`) quedaron **explícitamente disponibles como contexto potencial para una fase posterior** (p. ej. "personalización de tono o canal dentro de una intervención ya decidida por comportamiento"), pero nunca como base de un segmento.
- `docs/06_DECISION_LOGIC.md` §1: "esas dimensiones quedan disponibles como contexto secundario para una futura personalización (Fase 7+), no como entrada de esta política."
- `docs/07_AGENT_DESIGN.md` §8: la Email/HTML Skill ya existe, vive dentro del Action Agent, recibe `need`+`decision` y produce `subject + html + text`. No estaba definido, hasta ahora, si podía consumir algo más que eso.

**Pregunta que responde esta fase:** ¿el sistema necesita un agente nuevo que decida personalización por `use_case` u otro atributo WHO, o esa capacidad vive en otro lugar de la arquitectura ya cerrada?

---

## 2. Decisión cerrada: no se crea un Personalization Agent

**No se agrega un agente nuevo.** Dos razones, ambas ya presentes en el propio proyecto:

1. **Separación de responsabilidades (`docs/07_AGENT_DESIGN.md` §3):** un agente existe porque tiene una responsabilidad de negocio propia y distinta — Decision Agent decide, Action Agent ejecuta. Ajustar el tono o los ejemplos de un mensaje no es una decisión de negocio nueva, es una variación de **cómo se ejecuta** una decisión que el Decision Agent ya tomó. Eso es, por definición, una **Skill** (capacidad reutilizable interna a un agente), no un agente.
2. **La señal no lo justifica todavía:** `use_case` es, según el propio diagnóstico, la señal WHO más débil de las seis disponibles. Construir un componente nuevo de arquitectura alrededor de la señal más débil contradice el principio que ya gobierna todo el proyecto (`02_DATA_GENERATION_SPEC.md` §1, `04_DIAGNOSTIC_FINDINGS.md` §6): no se sobre-construye sobre una asociación débil, y ninguna dimensión WHO —individualmente— explica por sí sola Activation o conversión.

**Decisión cerrada:** la personalización por contexto WHO se implementa como una **extensión de la Email/HTML Skill** ya existente dentro del Action Agent (`docs/07_AGENT_DESIGN.md` §8), no como un componente nuevo.

---

## 3. Qué cambia en la Email/HTML Skill

### 3.1 Input extendido

| Campo | Origen | Obligatorio | Uso |
|---|---|---|---|
| `need` | Decision Agent | Sí | Define el contenido central del mensaje — sin cambios respecto a `07_AGENT_DESIGN.md` §8 |
| `decision` | Decision Agent | Sí | Define la acción que el mensaje debe motivar — sin cambios |
| `who_context` *(nuevo)* | HubSpot, vía el mismo `get_hubspot_contact` que ya usa el Decision Agent | No — opcional | Ajusta tono, ejemplos o encabezado del mensaje; **nunca su contenido central** |

`who_context` es un subconjunto de los atributos ya disponibles en el contacto de HubSpot (`docs/08A_INTEGRATION_SETUP.md` §2.3): `cm_role`, `cm_use_case`, `cm_industry`, `cm_company_size`, `cm_country`, `cm_acquisition_channel`. No se agrega ninguna property nueva a HubSpot — ya existen.

### 3.2 Ejemplo de lo que sí cambia y lo que no cambia

Para un usuario en Segmento 3 (`need`: "dar el salto de explorar el producto a construir su primer dashboard"), con `cm_use_case = "Marketing Analytics"` vs. `cm_use_case = "Sales/Revenue Analytics"`:

- **No cambia:** el segmento, la necesidad, la decisión, el `action_type`, ni el llamado a la acción central ("construye tu primer dashboard").
- **Sí puede cambiar:** el ejemplo o encabezado del mensaje — p. ej. mencionar un dashboard de campañas para el primer caso, o de pipeline para el segundo. Es una variación de ejemplo/tono, no una necesidad ni una promesa distinta.

### 3.3 Límite explícito — qué NO puede hacer `who_context`

- No cambia `need` ni `decision` recibidos del Decision Agent.
- No cambia `action_type` ni decide canal — sigue siendo exclusivo del Action Agent (`docs/07_AGENT_DESIGN.md` §5).
- No introduce una urgencia, promesa o necesidad ajena a la `decision` recibida — la misma regla que ya rige la Skill sin personalización (`docs/07_AGENT_DESIGN.md` §8: "el contenido debe ser trazable a la decisión/necesidad recibida").
- No usa `converted_to_paid` de ninguna forma.
- No es obligatorio: si `who_context` no está disponible o está incompleto para un usuario, la Skill produce el mensaje base sin personalizar — nunca bloquea el envío.

### 3.4 Quién puede invocar esta versión extendida

Exactamente el mismo llamador que ya existía: únicamente el Action Agent, únicamente cuando `action_type = user_email` (`docs/07_AGENT_DESIGN.md` §8). No cambia quién invoca la Skill, solo qué contexto opcional puede pasarle.

---

## 4. Relación con la Fase 8B (aprendizaje)

La capa de medición de `docs/08B_TRIGGER_AND_LEARNING.md` §3.2 ya prevé comparar variantes de copy cuando existan ("Comparación entre variantes de copy/canal, cuando existan — Fase 8B+"). Esta fase 8C es precisamente el origen de esas variantes: si en el futuro se generan versiones de copy distintas por `use_case`, la capa de medición de la Fase 8B es la que determina —con revisión humana, nunca de forma automática— si una variante funciona mejor que otra. La Email/HTML Skill no decide eso; solo produce las variantes que existan.

---

## 5. Qué queda explícitamente fuera de esta fase

- Copy real y específico por `use_case`/`role`/`industria` — esta fase especifica el mecanismo, no redacta el contenido.
- Cualquier lógica de decisión basada en WHO — sigue prohibida en el Decision Agent (`docs/07_AGENT_DESIGN.md` §4) y no se traslada aquí.
- Personalización dentro de la rama `internal_operational_action` (Slack) — esa comunicación es interna/operativa, no está dirigida al usuario final, y no tiene el mismo caso de uso de tono/ejemplo.
- Medición de si la personalización mejora resultados — corresponde a la capa de medición ya especificada en `docs/08B_TRIGGER_AND_LEARNING.md`.

---

Este documento cierra la pregunta de si hace falta un agente de personalización: no hace falta, porque personalizar tono por contexto WHO es una capacidad de ejecución, no una decisión de negocio nueva — y por eso vive dentro de una Skill ya existente, con límites explícitos, no como una pieza nueva de la arquitectura.
