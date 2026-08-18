# 06_DECISION_LOGIC.md — Lógica de decisión (Fase 6)

> Fuente de verdad de la Fase 6 — Decidir (`CLAUDE.md`, Fase 6). Traduce los 5 segmentos ya cerrados en `docs/05_SEGMENTATION.md` en una política de decisión: estado observable → necesidad → decisión → condición de salida → resultado de lifecycle que indica éxito. No reabre diagnóstico ni segmentación, no crea subsegmentos, no usa `converted_to_paid` para decidir. No define canales, mensajes, prompts de agente, timing ni automatizaciones — eso corresponde a las Fases 7 y 8.

---

## 1. Punto de partida

Esta fase parte de dos documentos ya cerrados y no los reinterpreta:

- `docs/04_DIAGNOSTIC_FINDINGS.md`: no hay un único bottleneck (Hallazgo 2); el comportamiento (WHAT) es la señal dominante, no los atributos WHO (Hallazgo 3); Activation y Late Value no difieren en conversión (Hallazgo 1), por lo que la política no distingue entre llegar rápido o tarde a First Value — solo entre llegar o no llegar.
- `docs/05_SEGMENTATION.md`: los 5 segmentos, definidos por dónde se detiene cada usuario en el funnel observable, con su necesidad ya descrita por segmento.

**Regla de esta fase:** la decisión se deriva del segmento/estado observable del usuario, no de atributos WHO (`country`, `role`, `industry`, `acquisition_channel`, `company_size`, `use_case`). Esas dimensiones quedan disponibles como contexto secundario para una futura personalización (Fase 7+), no como entrada de esta política.

**Regla sobre timing:** ningún documento cerrado hasta ahora (`CLAUDE.md`, diagnóstico, segmentación) fija un umbral de tiempo de inactividad para disparar una intervención. Por tanto, esta fase no inventa umbrales (2, 3, 7, 14 días, etc.). La señal de entrada de cada regla es el **estado/milestone observado**, no un tiempo transcurrido. Después de cuántos días intervenir, la frecuencia, los reintentos, la prioridad temporal, el canal y el mensaje quedan explícitamente fuera de esta fase.

**Regla sobre `converted_to_paid`:** no aparece en ninguna señal de entrada, decisión ni condición de salida de esta tabla. Es un resultado downstream que en fases posteriores permitirá medir impacto de negocio, no un criterio de decisión de esta política.

---

## 2. Tabla de decisión

| Segmento | Estado observable | Señal de entrada (evento/dato en `events.csv` / `users.csv`) | Necesidad | Decisión que debe tomar el sistema | Condición de salida (evento observable) | Resultado de lifecycle que indica éxito |
|---|---|---|---|---|---|---|
| **1. Sin enganche real** | Completó `registration_completed`, sin ningún evento posterior significativo de producto | Existe `registration_completed` para el `user_id`; no existe ningún evento posterior de las familias Onboarding, First Value o Behavior para ese `user_id` | Un motivo para volver y empezar a usar el producto | Determinar que el usuario necesita reenganche hacia el primer uso del producto | Aparece cualquier evento posterior a `registration_completed` para ese `user_id` (p. ej. `session_started`, `onboarding_started`) → el usuario deja de pertenecer al Segmento 1 y se reevalúa según su nuevo estado | Regreso al producto / primer evento post-signup relevante |
| **2. Estancado en onboarding** | Tiene `onboarding_started` y/o `profile_completed`, sin `onboarding_completed` | Existe `onboarding_started` para el `user_id`; no existe `onboarding_completed` | Completar la configuración inicial | Determinar que el usuario necesita completar onboarding | Aparece `onboarding_completed` para ese `user_id` | `onboarding_completed` |
| **3. Configurando, sin dashboard todavía** | Completó onboarding y/o conectó fuente, sin `dashboard_created` | Existe `onboarding_completed` y/o `data_source_connected`; no existe `dashboard_created` | Dar el salto de explorar el producto a construir su primer dashboard | Determinar que el usuario necesita avanzar hacia la creación del primer dashboard | Aparece `dashboard_created` para ese `user_id` | `dashboard_created` |
| **4. Dashboard creado, sin insight** | Tiene `dashboard_created`, sin `insight_viewed` que complete la secuencia de First Value | Existe `dashboard_created`; no existe `insight_viewed` posterior a los otros dos milestones de First Value | Encontrar o completar el paso final hacia un insight accionable | Determinar que el usuario necesita completar el camino hacia First Value mediante la visualización del primer insight | Aparece `insight_viewed` que completa la secuencia de First Value (junto con `data_source_connected` y `dashboard_created` previos) para ese `user_id` | First Value (los tres milestones completos) |
| **5. Llegó a First Value** | Completó la secuencia de First Value (`data_source_connected` + `dashboard_created` + `insight_viewed`), dentro o después de los 7 días | Los tres eventos de First Value existen para el `user_id`, sin importar el orden ni el tiempo transcurrido desde `registration_completed` | No aplica dentro del alcance de Onboarding & Activation | No existe una decisión de onboarding/activation pendiente para este segmento | N/A — no hay decisión activa que cerrar | N/A dentro de este journey |

---

## 3. Verificación de criterio de calidad

Para cada segmento, las cinco preguntas del criterio de calidad quedan respondidas explícitamente en la tabla:

1. **¿Cómo sé que está en este estado?** → columna "Señal de entrada", reconstruible únicamente con eventos de `events.csv` ya presentes en el dataset (verificado: `registration_started`, `registration_completed`, `onboarding_started`, `profile_completed`, `onboarding_completed`, `data_source_connected`, `dashboard_created`, `insight_viewed`, `session_started`, `dashboard_viewed`, `feature_used`, `dashboard_shared` son exactamente los `event_name` presentes en `data/events.csv`).
2. **¿Qué necesita?** → columna "Necesidad", heredada literalmente de `docs/05_SEGMENTATION.md` sin reinterpretación.
3. **¿Qué decisión debe tomar el sistema?** → columna "Decisión que debe tomar el sistema", expresada como determinación de necesidad, no como intervención, canal ni timing.
4. **¿Qué evento demuestra que la decisión ya no aplica?** → columna "Condición de salida", en todos los casos (salvo Segmento 5) un evento observable y no un juicio subjetivo.
5. **¿Cómo sé que la intervención tuvo éxito?** → columna "Resultado de lifecycle que indica éxito", en todos los casos un avance de milestone de producto, nunca una métrica de comunicación (apertura, clicks, engagement con un mensaje).

Ningún segmento requirió inventar una señal, un umbral de tiempo o un subsegmento para completar la tabla.

---

## 4. Qué queda explícitamente fuera de esta fase

- Canales de comunicación (email, WhatsApp, in-app, etc.).
- Mensajes, copy o tono.
- Prompts o diseño de agentes de IA.
- Timing de intervención: después de cuántos días intervenir, frecuencia, reintentos, prioridad temporal — no hay evidencia cerrada que respalde ningún umbral.
- Personalización por atributos WHO (`country`, `role`, `acquisition_channel`, `industry`, `company_size`, `use_case`) — quedan disponibles como contexto secundario, no como entrada de esta política.
- Uso de `converted_to_paid` en cualquier punto de la política — se mantiene exclusivamente como resultado downstream para medir impacto de negocio en fases posteriores, consistente con `CLAUDE.md` §7 y §12.
- Journey posterior a First Value (adopción, expansión, conversión) para el Segmento 5 — fuera del alcance de Onboarding & Activation (`docs/01_CONTEXT.md` §22).

---

Esta política constituye la fuente de verdad que será utilizada en la Fase 7 para diseñar el/los agentes que ejecutarán estas decisiones automáticamente.
