# 08B_TRIGGER_AND_LEARNING.md — Forma técnica del trigger y ciclo de aprendizaje (Fase 8B)

> Fuente de verdad de la Fase 8B — Trigger y Aprendizaje (`CLAUDE.md`, Fase 8, continuación de `docs/08A_INTEGRATION_SETUP.md`). Resuelve los dos puntos que `docs/07_AGENT_DESIGN.md` §18 y `docs/08A_INTEGRATION_SETUP.md` §7 dejaron explícitamente pendientes: **la forma técnica del trigger** (cuándo se invoca el Decision Agent) y **qué significa "Aprender"** en la cadena de `CLAUDE.md` §1, que hasta ahora no se había operacionalizado. No reinterpreta diagnóstico, segmentación, política de decisión ni la arquitectura de agentes ya cerrada — construye sobre ellas.

---

## 1. Punto de partida

Esta fase parte de tres documentos ya cerrados y no los reinterpreta:

- `docs/06_DECISION_LOGIC.md`: la tabla de decisión, donde cada segmento tiene una señal de entrada y una condición de salida definidas como **eventos observables concretos**, nunca como umbrales de tiempo.
- `docs/07_AGENT_DESIGN.md`: Decision Agent decide, Action Agent ejecuta; el ciclo completo (§14, Lifecycle Loop) ya describe que `update_hubspot_contact` alimenta la siguiente lectura del Decision Agent.
- `docs/08A_INTEGRATION_SETUP.md` §7: deja explícitamente para después "timing, frecuencia, reintentos, forma técnica del trigger" — exactamente lo que resuelve la sección 2 de este documento.

**Pregunta que responde esta fase:** ¿bajo qué mecanismo técnico se decide *cuándo* correr el Decision Agent sobre un usuario, y qué necesita existir para que la cadena `CLAUDE.md` termine de verdad en "Aprender" y no se quede en "Intervenir"?

---

## 2. El trigger: por qué ni evento puro ni solo por lote

### 2.1 Por qué no "cada evento, siempre"

`events.csv` (y, en producción, la tabla `events` de Supabase) produce eventos de forma constante y en volumen alto — sesiones, vistas de dashboard, uso de features. La tabla de decisión de `docs/06_DECISION_LOGIC.md` clasifica el segmento de un usuario únicamente a partir de la **presencia o ausencia** de un subconjunto pequeño de eventos (`registration_completed`, `onboarding_started`, `onboarding_completed`, `data_source_connected`, `dashboard_created`, `insight_viewed`). Ningún evento de la familia Behavior (`session_started`, `dashboard_viewed`, `feature_used`, `dashboard_shared`) cambia el segmento de un usuario por sí solo.

**Decisión cerrada:** correr el Decision Agent en cada evento sin distinción produciría invocaciones redundantes — un usuario puede generar varios eventos de Behavior en una sola sesión sin que su segmento cambie una sola vez. El trigger no se dispara por "cualquier evento", se dispara por los **eventos que la tabla de decisión usa como señal de entrada o de salida**, y solo esos.

### 2.2 Por qué tampoco alcanza con un lote diario

El Segmento 1 ("Sin enganche real", `docs/05_SEGMENTATION.md` §2.1) se define por la **ausencia** de cualquier evento posterior a `registration_completed`. Ningún evento puede disparar la detección de "no pasó nada" — por definición, no hay evento que observar. Un trigger exclusivamente basado en eventos nunca podría identificar a estos usuarios ni reaccionar cuando corresponde.

### 2.3 Decisión cerrada: modelo híbrido

| Mecanismo | Cuándo corre | Qué detecta | Qué NO detecta |
|---|---|---|---|
| **Trigger por evento** (event-driven) | Al ocurrir cualquiera de los eventos que la tabla de decisión usa como señal de entrada o salida (`registration_completed`, `onboarding_started`, `onboarding_completed`, `data_source_connected`, `dashboard_created`, `insight_viewed`) | Transiciones activas entre segmentos 2→3→4→5, y la entrada inicial al Segmento 1 vía `registration_completed` | Estancamiento por inactividad (nadie genera un evento para avisar que no generó ningún evento) |
| **Barrido diario** (scheduled sweep, una vez al día) | A una hora fija, sobre toda la base de usuarios con estado activo | Usuarios que llevan tiempo sin ningún evento nuevo (Segmento 1 sostenido en el tiempo, y como red de seguridad si un trigger por evento se perdió) | No aporta nada nuevo sobre usuarios cuyo estado ya fue evaluado correctamente por el trigger por evento — es complemento, no reemplazo |

Ambos mecanismos invocan exactamente el mismo Decision Agent, con la misma tabla de `docs/06_DECISION_LOGIC.md`, sin ninguna regla adicional — el trigger decide *cuándo* preguntar, nunca *qué* responder. Esa separación es la misma que ya rige entre agentes y tools (`docs/07_AGENT_DESIGN.md` §3): el trigger no es un agente, no decide de negocio.

### 2.4 Idempotencia — obligatoria antes de ejecutar cualquier acción

Antes de que el Action Agent dispare una acción, debe comparar el segmento recién calculado contra `cm_lifecycle_segment` (el valor ya guardado en HubSpot del ciclo anterior, `docs/08A_INTEGRATION_SETUP.md` §2.3).

**Regla cerrada:** si el segmento no cambió respecto al ciclo anterior, el Action Agent no ejecuta una nueva acción. Solo se actúa cuando:

1. es la primera vez que el usuario recibe una clasificación (no existe `cm_lifecycle_segment` previo), o
2. el segmento recién calculado es distinto del guardado.

Esto evita el caso concreto que motivó esta fase: un usuario que abre varias sesiones sin avanzar de segmento no debe recibir el mismo mensaje de reenganche en cada sesión. La idempotencia es responsabilidad del Action Agent, no del Decision Agent — el Decision Agent siempre reporta el estado real, sin filtrar; el Action Agent decide si ese estado ya fue accionado.

### 2.5 Qué NO resuelve esta sección

- La hora exacta del barrido diario, el proveedor del scheduler (cron, función programada, cola de eventos) y su implementación de infraestructura — es una decisión de implementación técnica sin impacto en la lógica de negocio, se resuelve al construir, no aquí.
- Reintentos ante fallos de una tool (`send_email_resend`, `send_slack_notification`) — es manejo de errores de infraestructura, no una regla de negocio nueva.

---

## 3. El ciclo de aprendizaje: qué existe hoy y qué falta

### 3.1 Lo que ya existe: retroalimentación de estado, no aprendizaje

El ciclo ya descrito en `docs/07_AGENT_DESIGN.md` §14 —cada acción se registra en HubSpot y ese registro alimenta la siguiente lectura del Decision Agent— es **memoria de estado**: permite no repetir una acción y detectar automáticamente cuándo un usuario cumplió su condición de salida. Es una condición necesaria para que el sistema funcione sin intervención manual, pero no constituye el paso "Aprender" de la cadena de `CLAUDE.md` §1. Memoria de estado responde "¿qué le pasó a este usuario?"; aprendizaje responde "¿esta decisión, en general, está funcionando mejor que la anterior?" — son preguntas distintas y esta fase no las confunde.

### 3.2 Qué necesita existir para que "Aprender" sea real

Una capa de medición que agregue, a través del tiempo y por segmento/`action_type`, la relación entre una acción ejecutada y si su condición de salida (`docs/06_DECISION_LOGIC.md`, columna "Condición de salida") se cumplió después, y en cuánto tiempo. Como mínimo:

| Campo agregado | De dónde sale | Pregunta que responde |
|---|---|---|
| Tasa de cumplimiento de condición de salida, por segmento y `action_type`, en una ventana fija tras la acción | `cm_last_action_type`, `cm_last_action_timestamp` (HubSpot) cruzado con el evento de salida correspondiente en Supabase/`events.csv` | ¿Qué proporción de usuarios accionados avanza de segmento después de la intervención? |
| Tiempo mediano entre la acción y el cumplimiento de la condición de salida, por segmento | Igual que arriba, diferencia de timestamps | ¿Cuánto tarda en verse el efecto de esta intervención? |
| Comparación entre variantes de copy/canal, cuando existan (Fase 8B+) | Igual que arriba, agrupado por variante | ¿Una variante de mensaje mueve más usuarios que otra? |

**Regla cerrada, con la misma disciplina de gobierno que ya aplica el proyecto (`CLAUDE.md` §7):** esta capa de medición **no ajusta la política por sí sola**. Ningún agente reinterpreta `docs/06_DECISION_LOGIC.md` ni cambia copy, canal o segmento de forma automática a partir de estos resultados — eso sería romper exactamente la regla que ya gobierna al Decision Agent (`docs/07_AGENT_DESIGN.md` §4: "no puede reinterpretar `06_DECISION_LOGIC.md`"). El aprendizaje se cierra con una **revisión humana periódica** (mensual o al cierre de cada cohorte piloto, según el roadmap ya definido) que decide si una nueva versión de copy, canal o —en última instancia— de la política de decisión se documenta y cierra formalmente, de la misma manera en que se cerró cada fase anterior de este proyecto: con un documento, no con un ajuste silencioso dentro del agente.

### 3.3 El loop completo, actualizado

```
1.  Trigger (evento relevante o barrido diario) dispara el Decision Agent
2.  Decision Agent reconstruye estado → segmento → necesidad → decisión
3.  Action Agent verifica idempotencia contra cm_lifecycle_segment previo
4.  Si cambió (o es primera vez): ejecuta la acción, registra resultado
5.  update_hubspot_contact actualiza el estado
6.  Capa de medición (3.2) acumula: acción → ¿se cumplió la condición de salida? → ¿en cuánto tiempo?
7.  Revisión humana periódica interpreta esa agregación
8.  Si se decide un ajuste, se documenta como nueva versión de política (no como cambio silencioso del agente)
9.  El ciclo continúa con la política vigente (ajustada o no)
```

Los pasos 1-5 ya estaban descritos en `docs/07_AGENT_DESIGN.md` §14. Los pasos 6-8 son la operacionalización de "Aprender" que esta fase agrega.

---

## 4. Qué queda explícitamente fuera de esta fase

- Infraestructura concreta del scheduler del barrido diario y de los reintentos ante fallos de tools.
- Diseño de variantes de copy o experimentos A/B — solo se deja la estructura de medición que los haría comparables si existieran.
- Cualquier mecanismo de ajuste automático de la política (aprendizaje automático, bandits, etc.) — deliberadamente fuera de alcance; el proyecto mantiene el criterio humano como cierre de cada ciclo de aprendizaje, consistente con `CLAUDE.md` §4 (ninguna fase se ejecuta sin plan explícito aprobado).
- Implementación real de la capa de medición (tablas, dashboards) — esta fase entrega la especificación, no el artefacto construido, siguiendo el mismo patrón de `docs/08A_INTEGRATION_SETUP.md`.

---

Este documento cierra el vacío que `docs/07_AGENT_DESIGN.md` §18 y `docs/08A_INTEGRATION_SETUP.md` §7 dejaron abierto sobre trigger y aprendizaje. La arquitectura de agentes, sus límites y el resto de la integración técnica se mantienen sin cambios.
