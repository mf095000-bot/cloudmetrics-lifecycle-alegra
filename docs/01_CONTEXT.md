# 01_CONTEXT.md — Contexto del caso CloudMetrics

## 1. Propósito de este documento

Este documento existe para que cualquier persona o IA que llegue a este repositorio, sin haber participado en las decisiones previas, pueda entender qué es CloudMetrics, qué reto se está resolviendo, qué alcance se eligió y qué reglas conceptuales rigen el diagnóstico, el diseño de datos, el journey y los agentes que se construirán en fases posteriores.

Este documento **no es**:

- un diagnóstico;
- una estrategia de lifecycle;
- un journey;
- una especificación de automatización;
- una especificación de agentes de IA;
- un dataset;
- una presentación.

Es el contexto necesario para construir todas esas piezas después, en el orden que define `CLAUDE.md`.

Este documento se apoya en tres fuentes y no las duplica:

- **`CLAUDE.md`** — contrato de gobierno del repositorio: reglas de planificación, Definition of Done, fases del proyecto.
- **`docs/00_WORKING_DOCUMENT.md`** — documento de trabajo estratégico con el detalle operacional completo (schemas conceptuales, taxonomía de eventos, métricas, arquitectura del AI Decision Agent). Se referencia, no se repite.
- **Brief original de la prueba técnica** *(Lifecycle & Automation Marketing Leader, Q2 2026)* — fuente de los requisitos de la prueba. Se sintetiza aquí lo relevante para entender el caso, no se copia íntegro.

## 2. Contexto de CloudMetrics

> **[DEFINICIÓN DE TRABAJO PARA EL CASO — no es una empresa real]**

CloudMetrics es, para efectos de este ejercicio, una SaaS B2B de analítica empresarial que permite a las empresas:

1. conectar fuentes de datos;
2. construir dashboards;
3. obtener insights para tomar decisiones.

El brief autoriza explícitamente asumir variables adicionales de negocio (tipos de usuario, canales activos, volumen de contactos, estructura del CRM) y usar datos ficticios o simulados, ya que lo que se evalúa es la lógica del sistema, no la conexión a una empresa real.

**Perfiles de usuario asumidos** *(supuesto de trabajo, detallado en `docs/00_WORKING_DOCUMENT.md` §2.2)*: Marketing, Ventas/Revenue, Operaciones. Se usan como contexto para el diseño posterior de segmentos y mensajes, no como una taxonomía cerrada de mercado real.

**Modelo de negocio:** SaaS B2B → prueba gratuita → suscripción paga.

## 3. Contexto de la prueba técnica

El reto ("Lifecycle & Automation Marketing Leader", área Growth · Product Marketing) pide diseñar un sistema de comunicación omnicanal para CloudMetrics que conecte: datos de usuario, eventos de producto, CRM, canales de comunicación, agentes de IA, automatizaciones y medición.

El brief ofrece dos journeys posibles (Adquisición y Nurturing / Onboarding y Activación), pidiendo resolver uno a fondo o ambos si están justificados y conectados — y advierte explícitamente que un journey resuelto a fondo es preferible a dos resueltos de forma superficial.

Los criterios de evaluación declarados en el brief son: pensamiento sistémico, uso real de IA, capacidad de orquestación, orientación a negocio, liderazgo técnico y estratégico, y ejecución y claridad. Se registran aquí como marco de referencia del "qué debe demostrar el sistema", no como checklist operativo de este documento.

## 4. Alcance elegido: Onboarding & Activation

**Decisión cerrada.** De los dos journeys que ofrece el brief, este proyecto resuelve **Onboarding y Activación** a profundidad. El journey de Adquisición y Nurturing queda fuera de alcance (ver sección 22).

De los cuatro resultados de negocio que propone el brief (conversión MQL→SQL, reducir time-to-value en onboarding, adopción de features clave, recuperación de usuarios en riesgo), este proyecto persigue **reducir el time-to-value en onboarding**. Los otros tres quedan fuera del alcance primario.

## 5. Objetivo de negocio

El objetivo de negocio y la métrica operacional que lo opera se mantienen como dos cosas distintas:

- **Objetivo de negocio:** reducir el Time-to-Value durante Onboarding.
- **Métrica/comportamiento operacional prioritario:** aumentar la proporción de usuarios que alcanzan Activation dentro de los primeros 7 días desde signup.

La reducción del Time-to-Value es la intención de negocio; el aumento de la tasa de Activation en la ventana de 7 días es cómo se opera y mide esa intención dentro de este sistema.

**Hipótesis a validar, no conclusión:** se plantea que Activation podría estar asociada con una mayor probabilidad de conversión a paid. Esta asociación **no se asume como cierta**; es una de las preguntas que el diagnóstico (fase 4) deberá investigar con los datos, y `converted_to_paid` no se utiliza en ningún caso para definir Activation.

## 6. Preguntas que queremos poder responder con los datos

Estas son preguntas de análisis, **no conclusiones**:

1. ¿Dónde se pierde la mayor cantidad de usuarios en el funnel?
2. ¿Qué proporción inicia pero no completa el registro?
3. ¿Qué proporción completa el registro pero abandona durante onboarding?
4. ¿Cuánto tiempo tarda un usuario en realizar su primera acción significativa?
5. ¿Qué proporción alcanza First Value?
6. ¿Qué proporción alcanza Activation dentro de 7 días?
7. ¿Qué proporción alcanza First Value después de 7 días?
8. ¿Qué comportamientos están asociados con Activation?
9. ¿Qué comportamientos están asociados con conversión a paid?
10. ¿Activation está asociada con una mayor probabilidad de conversión a paid?

## 7. Lifecycle conceptual

El journey, a nivel conceptual, sigue esta secuencia temporal (no implica que todo usuario la recorra linealmente ni sin fricción):

```text
registration_started
→ registration_completed / signup
→ onboarding
→ First Action
→ data_source_connected
→ dashboard_created
→ insight_viewed
```

## 8. Funnel pre-account y Registration Abandonment

El funnel de Lifecycle **comienza antes de que exista una cuenta completa**. Debe distinguirse explícitamente entre:

- `registration_started`: la persona inició el proceso de registro.
- `registration_completed` / `signup`: la persona completó la creación de la cuenta.

**Registration Abandonment** — abandonar entre `registration_started` y `registration_completed` — es una señal relevante de onboarding y debe poder analizarse aunque la persona nunca haya llegado a existir como fila en `users.csv`. Su comportamiento se conserva en `events.csv` mediante identidad `anonymous_id`/`session_id` (`user_id = null`), tal como detalla `docs/00_WORKING_DOCUMENT.md` §15.

Este funnel de registro (Landing → Signup Started → Form Started → Form Progress → Signup Completed) es conceptualmente distinto del funnel de Onboarding/Activation que empieza después del signup — ambos se analizan por separado, sin asumir que todo abandono pre-cuenta es un problema de onboarding.

## 9. Signup y comienzo del reloj de Lifecycle

`registration_completed`/`signup_date` es el evento que marca el inicio del reloj de 7 días usado en la definición de Activation. Antes de ese momento, ese reloj no corre.

## 10. First Action

`first_action_timestamp` es una variable derivada (no observada) que representa la primera interacción significativa con el producto **después** del signup. El signup mismo no cuenta como First Action.

## 11. First Value

**Definición operacionalmente cerrada:**

> First Value = `data_source_connected` + `dashboard_created` + `insight_viewed`

Es una secuencia de tres eventos, no una alternativa entre ellos — completar solo uno o dos no constituye First Value. First Value **no depende de la ventana de 7 días**: un usuario que completa la secuencia en el día 12 igualmente alcanzó First Value.

## 12. Activation

> Activation = First Value completado dentro de los primeros 7 días desde signup.

## 13. Late Value

> Late Value = First Value completado después de los primeros 7 días.

No equivale a "nunca recibió valor" — el usuario sí experimentó el valor definido, solo que fuera de la ventana crítica.

## 14. Not Activated

> Not Activated = no ha completado First Value al momento del análisis.

Es un estado potencialmente temporal (el usuario podría aún alcanzar First Value más adelante y convertirse en Late Value), a diferencia de Late Value, que es un estado ya consolidado.

## 15. Activation vs. First Value

| | Pregunta que responde | Depende del tiempo |
|---|---|---|
| **First Value** | ¿Alguna vez experimentó el valor definido? | No |
| **Activation** | ¿Experimentó ese valor dentro de los primeros 7 días? | Sí (ventana de 7 días) |

Son dos ejes distintos, no sinónimos. Activation no equivale a ejecutar solo una de las tres acciones de la secuencia de First Value; requiere las tres, y además dentro del plazo. Late Value y Not Activated tampoco son equivalentes entre sí ni intercambiables con Activation.

## 16. Datos observados vs. variables derivadas

**Observados / iniciales** (van en el dataset crudo):

- Atributos de usuario en `users.csv`.
- Eventos crudos en `events.csv`, incluyendo eventos previos al signup completo (p. ej. `registration_started`).
- `converted_to_paid`, como resultado downstream observado.

**Derivados** (se calculan después, nunca se generan a mano ni se embeben en el dataset inicial):

- `lifecycle_stage`
- `first_action_timestamp`
- `first_value_date`
- `days_to_first_value`
- `activation_status`
- `activation_score`
- métricas de funnel
- segmentos

**Regla explícita:** si no se puede derivar de datos crudos, no es válido. El detalle ampliado de variables derivadas por categoría (registro, onboarding, comportamiento temprano, valor, activación, diagnóstico comportamental) está en `docs/00_WORKING_DOCUMENT.md` §26-27.

## 17. Rol de `users.csv`

`users.csv` representará exclusivamente a personas que **completaron el registro y tienen una cuenta creada**. Una persona que inicia el formulario pero abandona antes de crear la cuenta no aparecerá aquí — su comportamiento pre-account queda en `events.csv`.

El esquema exacto de columnas, tipos y valores de ejemplo **no se define en este documento**; se define en `02_DATA_GENERATION_SPEC.md`.

## 18. Rol de `events.csv`

`events.csv` es la fuente principal para reconstruir el comportamiento, tanto de personas sin cuenta (`user_id = null`, identificadas por `anonymous_id`/`session_id`) como de usuarios con cuenta creada, en cualquier estado del funnel.

El esquema exacto de columnas y la taxonomía exhaustiva de eventos con su metadata **no se definen en este documento**; se definen en `02_DATA_GENERATION_SPEC.md`.

## 19. Taxonomía conceptual de eventos

A nivel de familias (sin exhaustividad — el detalle completo va en `02_DATA_GENERATION_SPEC.md`):

- **Entrada y registro:** `landing_viewed`, `signup_started`, `signup_form_started`, `signup_form_field_completed`, `signup_abandoned`, `signup_completed`.
- **Onboarding:** `onboarding_started`, `profile_completed`, `onboarding_completed`.
- **First Value:** `data_source_connected`, `dashboard_created`, `insight_viewed`.
- **Comportamiento y adopción posterior:** `session_started`, `dashboard_viewed`, `feature_used`, `dashboard_shared` (fuera del foco principal de Onboarding & Activation, pero relevantes para la señal downstream de conversión).

## 20. Qué NO debemos asumir antes del diagnóstico

No se determina todavía, y no debe determinarse hasta después de la fase de diagnóstico (fase 4) y segmentación (fase 5):

- cuál es el bottleneck del funnel;
- cuál es el segmento prioritario;
- qué intervención funciona mejor;
- qué canal usar;
- qué agente de IA debe construirse;
- cuál es el journey definitivo.

## 21. Principios del sistema

Toda la construcción posterior sigue esta cadena:

```text
Observar → Calcular → Diagnosticar → Segmentar → Decidir → Intervenir → Medir → Aprender
```

Y mantiene esta separación estricta en todo momento:

```text
OBSERVADO → DERIVADO → DIAGNÓSTICO → DECISIÓN
```

## 22. Límites del alcance actual

Quedan fuera del alcance de este proyecto:

- el journey de **Adquisición y Nurturing** (segunda opción del brief, no elegida);
- retención post-activación y expansión/upsell;
- churn de usuarios ya convertidos a paid;
- los otros tres resultados de negocio del brief no elegidos como objetivo primario (conversión MQL→SQL, adopción de features clave, recuperación de usuarios en riesgo de abandono fuera del contexto de onboarding).

## 23. Stack de referencia

> **[DECISIÓN APROBADA EN CONVERSACIÓN — no proviene del brief ni del Working Document original]**

- **GitHub:** fuente de verdad y documentación del proyecto.
- **Claude Code:** construcción y orquestación del sistema.
- **HubSpot:** CRM y ejecución de lifecycle/automation.
- **Resend:** envío de emails.
- **Agentes de IA:** capa de decisión del sistema.

La implementación exacta de cada componente no se diseña todavía. El diagnóstico y el journey determinarán qué automatizaciones y agentes se necesitan (fases 7 y 8 de `CLAUDE.md`).

## 24. Entregable final del caso

> **[DECISIÓN APROBADA EN CONVERSACIÓN]**

El entregable final de la prueba técnica consistirá en:

- **Video 1 — Sistema + Journeys** (máx. 10 min): diagnóstico, arquitectura del sistema, journeys corriendo en vivo, métricas, roadmap 30/60/90.
- **Video 2 — Capa de IA** (máx. 5 min): agentes construidos, herramientas e integración, prompts y lógica.
- **Presentación HTML interactiva** como material de apoyo.
- **Repositorio GitHub** como documentación y soporte técnico del sistema.

La Fase 10 de `CLAUDE.md` se interpretará en consecuencia como: *"Preparación del paquete final de entrega: presentación HTML de apoyo + documentación + assets/guiones necesarios para los dos videos obligatorios."* Esta reinterpretación queda registrada aquí; `CLAUDE.md` no se modifica todavía.

## 25. Dependencias hacia `02_DATA_GENERATION_SPEC.md`

Quedan explícitamente abiertos para el siguiente documento:

- esquema exacto de columnas de `users.csv` y `events.csv` (tipos, ejemplos, valores permitidos);
- taxonomía exhaustiva de eventos con su metadata;
- volumetría (10.000 usuarios) y periodo temporal a simular;
- valor de X (minutos de inactividad) para la regla de `signup_abandoned`;
- tasas de fricción a modelar en cada etapa del funnel, sin fabricar patrones que confirmen un bottleneck de antemano.
