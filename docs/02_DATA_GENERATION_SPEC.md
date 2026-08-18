# 02_DATA_GENERATION_SPEC.md — Especificación de generación de datos

## 0. Relación con otros documentos

Esta especificación traduce las definiciones conceptuales de `docs/01_CONTEXT.md` en un esquema de datos generable y reproducible. No repite el contexto de negocio, las definiciones protegidas ni el detalle operacional ya cubierto en `CLAUDE.md` y `docs/00_WORKING_DOCUMENT.md` — los referencia.

Esta especificación define **qué campos y eventos existen y por qué**. No define **cuántos usuarios caen en cada caso ni con qué probabilidad** — eso es un documento posterior de parámetros de distribución, deliberadamente separado (ver sección 17).

---

## 1. Propósito y principios

El dataset debe permitir **observar** el comportamiento de los usuarios, no interpretarlo. Cuatro principios rectores:

1. **Solo observación.** `users.csv` y `events.csv` contienen únicamente hechos que ocurrieron en la simulación (atributos declarados, eventos con timestamp). Ninguna columna representa una conclusión, un estado calculado o una etiqueta interpretativa.
2. **Sin variables derivadas embebidas.** Ninguna de las variables listadas en `CLAUDE.md` §6 (`lifecycle_stage`, `first_action_timestamp`, `first_value_date`, `days_to_first_value`, `activation_status`, `activation_score`, métricas de funnel, segmentos) aparece en los datasets generados. Se calculan después, en la fase de diagnóstico, a partir de estos datos crudos.
3. **El generador no conoce el bottleneck.** El proceso de generación no está diseñado para producir un resultado diagnóstico predeterminado. Las tasas y distribuciones que gobiernan cuántos usuarios abandonan, tardan o nunca llegan a First Value se definen en una etapa posterior y separada de esta especificación (sección 17), precisamente para que esta spec no se contamine con un resultado ya decidido.
4. **Toda variable y todo evento tiene una razón analítica.** Ningún campo se incluye porque "sea fácil de generar" o "pueda ser útil algún día". Cada uno debe responder a una pregunta concreta de `01_CONTEXT.md` §6 o del Working Document §38.

---

## 2. Arquitectura de datos

| | `users.csv` | `events.csv` |
|---|---|---|
| Qué representa | Cuentas creadas (registro completado) | Comportamiento observado, con y sin cuenta |
| Universo | Subconjunto: solo quienes completan `registration_completed` | Superconjunto: incluye identidades que nunca completan el registro |
| Granularidad | 1 fila = 1 usuario | 1 fila = 1 evento |
| Relación | — | N eventos → 1 usuario (vía `user_id`, cuando existe) |

**Regla de pertenencia:** una persona que abandona el registro antes de `registration_completed` **no tiene fila en `users.csv`**. Su comportamiento vive exclusivamente en `events.csv`, identificado por `anonymous_id`/`session_id` con `user_id = null`. Esto es lo que hace posible analizar Registration Abandonment sin ensuciar `users.csv` con cuentas que nunca existieron.

**Qué NO debe estar en ninguno de los dos datasets:**

- Cualquier variable derivada de la lista prohibida (`CLAUDE.md` §6).
- Campos calculados: edades derivadas de fechas, ratios, scores, clasificaciones de estado (activado/no activado/etc.).
- Texto libre no estructurado fuera del campo `metadata` (que es JSON acotado por evento, no texto abierto).
- Cualquier campo cuya única función sea anticipar una conclusión de diagnóstico (p. ej. una bandera `is_bottleneck_user`).

---

## 3. Schema definitivo de `users.csv`

`users.csv` representa exclusivamente personas que completaron el registro y tienen una cuenta creada.

| Campo | Tipo | Ejemplo | Definición | Observado / derivado | Reglas de generación | Restricciones |
|---|---|---|---|---|---|---|
| `user_id` | string | `U00001` | Identificador único de la cuenta | Observado | Se asigna únicamente cuando ocurre `registration_completed` en `events.csv` para esa identidad | Único; obligatorio; formato consistente en todo el dataset |
| `first_name` | string | `María` | Nombre declarado en el registro | Observado | Generado de un catálogo de nombres con variabilidad por país | No nulo |
| `last_name` | string | `Gómez` | Apellido declarado | Observado | Igual que `first_name` | No nulo |
| `email` | string | `maria@empresa.com` | Email asociado a la cuenta | Observado | Derivado del nombre + dominio ficticio de empresa; no debe usarse un dominio real | Único; formato de email válido |
| `country` | string | `Colombia` | País declarado | Observado | Catálogo de países con presencia B2B plausible para el caso | No nulo |
| `signup_date` | datetime | `2026-08-01 09:32:14` | Momento en que se crea la cuenta | Observado | Debe ser exactamente el timestamp del evento `registration_completed` de esa identidad en `events.csv` — no se genera de forma independiente | No nulo; posterior o igual al `registration_started` de la misma identidad |
| `role` | string | `Marketing Manager` | Rol declarado por el usuario | Observado | Catálogo de roles alineado con los 3 perfiles de `01_CONTEXT.md` §2 (Marketing, Ventas/Revenue, Operaciones) | No nulo |
| `industry` | string | `SaaS` | Industria declarada | Observado | Catálogo de industrias plausibles para un comprador B2B de analítica | No nulo |
| `company_size` | string | `51–200` | Tamaño de empresa declarado | Observado | Catálogo de rangos estándar (p. ej. 1–10, 11–50, 51–200, 201–1000, 1000+) | No nulo |
| `use_case` | string | `Marketing Analytics` | Caso de uso declarado al registrarse | Observado | Catálogo de casos de uso coherente con los 3 perfiles de usuario | No nulo |
| `acquisition_channel` | string | `Organic Search` | Canal de adquisición | Observado | Catálogo de canales (orgánico, pago, referido, directo, etc.) | No nulo |
| `converted_to_paid` | boolean/integer | `0` | Si la cuenta convirtió a pago posteriormente | Observado / resultado downstream | Ver sección 9.1 — mecanismo de generación no definido todavía en esta spec; se define en la etapa de parametrización, sin imponer una relación determinista con Activation | No nulo (0 o 1) |

**Confirmación explícita — variables que NO se agregan a `users.csv`:** `lifecycle_stage`, `first_action_timestamp`, `first_value_date`, `days_to_first_value`, `activation_status`, `activation_score`. Ninguna excepción.

---

## 4. Schema definitivo de `events.csv`

| Campo | Tipo | Ejemplo | Justificación |
|---|---|---|---|
| `event_id` | string | `E0000001` | Identificador único de la fila; necesario para trazabilidad y para poder referenciar un evento específico durante la validación |
| `event_name` | string | `data_source_connected` | Nombre estandarizado del evento (ver taxonomía, sección 6) |
| `event_timestamp` | datetime | `2026-08-01 09:28:41` | Momento exacto del evento; base de toda la reconstrucción temporal (funnel, First Value, Time to First Action) |
| `user_id` | string / null | `U00001` / `null` | Vincula el evento a una cuenta creada; `null` para comportamiento pre-account |
| `anonymous_id` | string | `A8F92K` | Identificador persistente de la identidad antes (y después) de crear cuenta; permite reconstruir Registration Abandonment y el journey completo de un usuario incluso antes de tener `user_id` |
| `session_id` | string | `S9D21X` | Identificador de sesión; permite analizar comportamiento dentro de una misma visita, distinto de comportamiento entre sesiones |
| `metadata` | JSON | `{"source_type": "google_analytics"}` | Contexto específico del evento — ver reglas de la sección 4.1 |

### 4.1 Regla única de metadata

Se mantiene **una sola columna `metadata`** en formato JSON, en vez de columnas específicas por tipo de evento.

**Definición:** `metadata` contiene exclusivamente **contexto observable del evento** — un hecho específico que ocurrió en el momento de ese evento y que fue registrado tal cual, sin interpretación. No contiene nunca un estado calculado, una clasificación, un score o una conclusión derivada de otros eventos.

**Prohibido explícitamente en `metadata`:** cualquier variable derivada de `CLAUDE.md` §6 o equivalente — incluyendo, sin limitarse a, `activation_status`, `days_to_first_value`, `first_value_date`, `first_action_timestamp`, `lifecycle_stage`, `activation_score`, cualquier segmento, cualquier bandera de tipo "es bottleneck" o "es prioritario", y cualquier resultado de comparación temporal (p. ej. "llegó a tiempo"/"llegó tarde").

**Ejemplos válidos** (contexto observable, propio del evento):

```json
{"source_type": "google_analytics"}
```
```json
{"feature": "filters"}
```
```json
{}
```

**Ejemplos NO válidos** (interpretación o estado derivado):

```json
{"activation_status": "activated"}
```
```json
{"days_to_first_value": 3}
```
```json
{"is_late": true}
```
```json
{"segment": "power_user"}
```

Reglas adicionales:

- Un evento puede tener `metadata = {}` (vacío) si no hay ninguna propiedad observable que agregue valor analítico — no se rellena metadata "porque sí".
- Cada propiedad de metadata debe estar justificada individualmente por una pregunta analítica en la tabla de taxonomía (sección 6), igual que cualquier columna.

### 4.2 Sobre `source`/`channel` a nivel de evento

**Decisión cerrada:** no se agrega una columna `source` o `channel` por defecto a todos los eventos. `acquisition_channel` en `users.csv` cubre la pregunta de canal de adquisición a nivel de usuario. Un atributo de canal a nivel de evento individual solo se evaluará, evento por evento, si existe una pregunta analítica específica que lo justifique (por ejemplo, si en el futuro quisiéramos distinguir en qué canal ocurrió una sesión de reactivación) — no se incluye de forma general en esta versión de la spec.

---

## 5. Identidad pre-account

```text
anonymous_id + session_id            (user_id = null)
        ↓
[si ocurre registration_completed]
        ↓
anonymous_id + session_id + user_id  (nuevo, asignado)
```

Reglas:

- Todo `anonymous_id` se genera en el primer evento de esa identidad (típicamente `registration_started`, si ese es el primer evento capturado para esa persona).
- Si la identidad completa el registro, **todos los eventos posteriores** de esa misma identidad llevan el `user_id` asignado.
- El `anonymous_id` original se conserva en todas las filas, incluso después de asignarse `user_id` — esto permite reconstruir el journey completo de un usuario desde antes de tener cuenta, uniendo por `anonymous_id`.
- Registration Abandonment se reconstruye filtrando `events.csv` por identidades (`anonymous_id`) que tienen `registration_started` pero ningún evento `registration_completed` asociado — sin necesidad de ningún campo derivado almacenado.

---

## 6. Taxonomía exhaustiva de eventos

**Esta taxonomía es el contrato definitivo para la generación de `events.csv`.** El generador solo puede producir los eventos aquí listados, con las propiedades aquí definidas. No se agregan eventos nuevos, ni se amplía la metadata permitida de un evento existente, sin modificar primero esta sección de esta spec — nunca directamente en el script de generación.

Cada evento se documenta con las 8 dimensiones que forman el contrato: nombre, familia, significado (definición operacional), momento respecto a signup, requisito de identidad (si requiere `user_id`), repetibilidad, metadata permitida, y pregunta analítica que responde. La columna "por qué existe" se mantiene como justificación adicional de diseño.

### 6.1 Familia: Registration

**Decisión cerrada:** únicamente estos dos eventos. No se agrega granularidad por campo de formulario (`signup_form_field_completed` queda descartado).

| Evento | `registration_started` |
|---|---|
| Familia | Registration |
| Definición operacional | La persona inicia el proceso de registro (primera interacción con el flujo de creación de cuenta) |
| Por qué existe | Es el punto de partida del funnel de Lifecycle, anterior a la existencia de una cuenta (`01_CONTEXT.md` §8) |
| Momento respecto a signup | Antes (es el evento que abre la ventana de registro) |
| Requiere `user_id` | No (`user_id = null`; identificado por `anonymous_id`) |
| Metadata permitida | Vacía o mínima (p. ej. no se define ninguna propiedad obligatoria en esta versión) |
| Repetible | No — una identidad inicia el registro una vez en el marco de esta simulación |
| Pregunta analítica | ¿Cuánta gente entra al funnel de registro? Base para calcular abandono de registro |

| Evento | `registration_completed` |
|---|---|
| Familia | Registration |
| Definición operacional | La persona completa la creación de la cuenta |
| Por qué existe | Marca la transición de identidad anónima a usuario con cuenta; es el evento que define `signup_date` y abre el reloj de Activation |
| Momento respecto a signup | Es el propio signup |
| Requiere `user_id` | Sí — este es el evento donde se asigna el `user_id` por primera vez |
| Metadata permitida | Vacía en esta versión |
| Repetible | No |
| Pregunta analítica | ¿Qué proporción de quienes inician registro lo completan? Base de `signup_date` para todo el resto del análisis |

### 6.2 Familia: Onboarding

| Evento | `onboarding_started` |
|---|---|
| Familia | Onboarding |
| Definición operacional | El usuario inicia el flujo de configuración posterior al signup |
| Por qué existe | Permite medir si, y cuándo, un usuario con cuenta empieza a interactuar con el producto tras registrarse |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Vacía en esta versión |
| Repetible | No |
| Pregunta analítica | ¿Qué proporción de cuentas inicia onboarding? ¿Cuánto tiempo transcurre entre signup y este evento? |

| Evento | `profile_completed` |
|---|---|
| Familia | Onboarding |
| Definición operacional | El usuario completa la configuración de su perfil dentro del onboarding |
| Por qué existe | Es un paso intermedio del onboarding que permite ubicar dónde ocurre la caída dentro de ese sub-funnel |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Vacía en esta versión |
| Repetible | No |
| Pregunta analítica | ¿Dónde ocurre la mayor caída dentro del onboarding? |

| Evento | `onboarding_completed` |
|---|---|
| Familia | Onboarding |
| Definición operacional | El usuario finaliza el proceso de onboarding |
| Por qué existe | Cierra el sub-funnel de onboarding y permite compararlo contra el inicio de la secuencia de First Value |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Vacía en esta versión |
| Repetible | No |
| Pregunta analítica | ¿Qué porcentaje de cuentas completa el onboarding? |

### 6.3 Familia: First Value

**Decisión cerrada:** estos tres eventos **son repetibles**. Activation se calculará posteriormente a partir de las primeras ocurrencias válidas necesarias para completar la secuencia — el dataset no almacena ningún estado derivado (ni siquiera implícitamente limitando a una sola ocurrencia).

| Evento | `data_source_connected` |
|---|---|
| Familia | First Value |
| Definición operacional | El usuario conecta una fuente de datos |
| Por qué existe | Es el primero de los tres milestones que constituyen First Value (`01_CONTEXT.md` §11) |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Propiedad observable del tipo de fuente conectada (p. ej. tipo de fuente), útil para investigar si algún tipo de fuente genera más fricción — a definir con precisión antes de generar |
| Repetible | Sí — un usuario puede conectar varias fuentes; la primera ocurrencia es la relevante para el cálculo posterior de First Value |
| Pregunta analítica | ¿Qué porcentaje alcanza este primer milestone? ¿Cuánto tarda desde signup? ¿Qué tipo de fuente se conecta primero? |

| Evento | `dashboard_created` |
|---|---|
| Familia | First Value |
| Definición operacional | El usuario crea un dashboard |
| Por qué existe | Segundo milestone de First Value |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Propiedad observable a evaluar (p. ej. si el dashboard usa una plantilla o se crea desde cero) — a definir antes de generar, solo si responde una pregunta analítica concreta |
| Repetible | Sí — la primera ocurrencia es la relevante para First Value |
| Pregunta analítica | ¿Qué proporción de quienes conectan una fuente llega a crear un dashboard? ¿Cuál es el milestone de mayor fricción dentro de la secuencia? |

| Evento | `insight_viewed` |
|---|---|
| Familia | First Value |
| Definición operacional | El usuario visualiza un insight accionable |
| Por qué existe | Tercer y último milestone que completa First Value |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | A evaluar; posible candidato: tipo de insight visualizado, si aporta una pregunta analítica concreta |
| Repetible | Sí — la primera ocurrencia que completa la secuencia (posterior a los otros dos milestones del mismo usuario) determina el momento de First Value |
| Pregunta analítica | ¿Qué proporción completa la secuencia completa? ¿Cuánto tarda el último paso respecto a los dos anteriores? |

### 6.4 Familia: Behavior (comportamiento y adopción posterior)

| Evento | `session_started` |
|---|---|
| Familia | Behavior |
| Definición operacional | El usuario abre una nueva sesión de producto |
| Por qué existe | Permite medir recurrencia y continuidad de uso, más allá del primer valor |
| Momento respecto a signup | Después (también puede aplicar antes de signup, para visitantes que exploran sin cuenta — a confirmar si se incluye para identidades pre-account) |
| Requiere `user_id` | No necesariamente — puede ocurrir con `user_id = null` si es una sesión de un visitante pre-account |
| Metadata permitida | Vacía en esta versión |
| Repetible | Sí, múltiples veces por usuario |
| Pregunta analítica | ¿Con qué frecuencia regresan los usuarios tras su primera sesión? |

| Evento | `dashboard_viewed` |
|---|---|
| Familia | Behavior |
| Definición operacional | El usuario visualiza un dashboard existente (no necesariamente el primero) |
| Por qué existe | Mide consumo continuo de valor, distinto de la creación inicial |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Vacía en esta versión |
| Repetible | Sí |
| Pregunta analítica | ¿El consumo posterior de dashboards se relaciona con la velocidad de Activation o con la conversión a pago? |

| Evento | `feature_used` |
|---|---|
| Familia | Behavior |
| Definición operacional | El usuario utiliza una funcionalidad específica del producto |
| Por qué existe | Permite analizar adopción de features más allá de la secuencia mínima de First Value |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | `{"feature": "..."}` — necesaria para no perder qué feature se usó; sin esto el evento pierde su valor analítico |
| Repetible | Sí |
| Pregunta analítica | ¿Qué features se asocian con mayor probabilidad de conversión a pago o con mayor retención? |

| Evento | `dashboard_shared` |
|---|---|
| Familia | Behavior |
| Definición operacional | El usuario comparte un dashboard con otra persona |
| Por qué existe | Señal de colaboración y expansión dentro de la cuenta, relevante para la hipótesis de conversión a pago (uso multi-usuario) |
| Momento respecto a signup | Después |
| Requiere `user_id` | Sí |
| Metadata permitida | Vacía en esta versión |
| Repetible | Sí |
| Pregunta analítica | ¿La colaboración temprana se asocia con mayor conversión a pago? |

**Nota de alcance:** la familia Behavior queda fuera del foco principal de Onboarding & Activation (`01_CONTEXT.md` §22), pero se incluye porque alimenta la pregunta analítica downstream sobre conversión a pago (`01_CONTEXT.md` §6, pregunta 9-10).

---

## 7. Reglas temporales

- `registration_started` ≤ `registration_completed`, cuando ambos existen para la misma identidad (`anonymous_id`).
- `signup_date` en `users.csv` debe ser exactamente el `event_timestamp` del `registration_completed` de esa identidad — no se genera de forma independiente en `users.csv` (evita inconsistencia entre los dos archivos).
- Ningún evento posterior al signup (`onboarding_*`, eventos de First Value, eventos de Behavior) puede tener `event_timestamp` anterior a `signup_date`.
- El momento de First Value se determinará en la fase de diagnóstico como el timestamp del evento que **completa** la secuencia de los tres milestones (la última de las tres primeras ocurrencias necesarias), no un orden fijo — el generador no debe forzar que los tres eventos ocurran siempre en el orden `data_source_connected → dashboard_created → insight_viewed`; el orden real puede variar entre usuarios.
- Activation/Late Value se determinan comparando ese momento contra `signup_date + 7 días` — cálculo de fase 4, no algo que se represente en los datos crudos.
- **Eventos repetibles:** `session_started`, `dashboard_viewed`, `feature_used`, `dashboard_shared`, `data_source_connected`, `dashboard_created`, `insight_viewed`.
- **Eventos de ocurrencia única por identidad:** `registration_started`, `registration_completed`, `onboarding_started`, `profile_completed`, `onboarding_completed`.
- Todo evento respeta orden cronológico estricto dentro de la misma identidad (no se generan timestamps fuera de secuencia lógica, p. ej. `onboarding_completed` antes de `onboarding_started`).

---

## 8. Definición de First Action

**Sin cerrar todavía**, tal como pediste. Lo que sí queda fijado en esta spec:

- `first_action_timestamp` **nunca se almacena como dato observado** en ningún dataset generado, bajo ninguna circunstancia. Es y seguirá siendo una variable derivada.
- El signup (`registration_completed`) **no cuenta** como First Action — esto sí está cerrado por `01_CONTEXT.md` §10 y `CLAUDE.md` §6.
- **Condición de cierre, antes del diagnóstico:** debe existir una definición operacional cerrada de qué eventos de la taxonomía (sección 6) constituyen "primera interacción significativa", y esa definición debe ser reconstruible **exclusivamente a partir de `events.csv`** — sin necesitar ningún campo adicional, bandera o metadata especial que no esté ya contemplada en el contrato de la sección 6. Mientras esa definición no esté cerrada, la fase de diagnóstico no puede calcular First Action de forma consistente.
- Qué eventos específicos califican queda pendiente hasta después de cerrada la taxonomía completa — se lista como punto abierto en la sección 17.

---

## 9. First Value y Activation — reconstruibilidad, no almacenamiento

Recordatorio operacional (no redefinición — las definiciones viven en `CLAUDE.md` §7 y `01_CONTEXT.md` §11-12):

> First Value = `data_source_connected` + `dashboard_created` + `insight_viewed`
> Activation = First Value completado dentro de los primeros 7 días desde `signup_date`.

Lo que esta spec garantiza es que el dataset generado haga esto **reconstruible**:

- Los tres eventos de First Value existen, son atribuibles al mismo `user_id`, y sus timestamps permiten calcular cuál ocurrió primero, segundo y tercero (dado que son repetibles, la reconstrucción debe tomar la primera ocurrencia de cada uno).
- No se almacena `first_value_date`, `days_to_first_value` ni `activation_status` en ningún archivo de esta fase.

### 9.1 `converted_to_paid`

`converted_to_paid` se mantiene como dato observado/downstream en `users.csv` (sección 3). Esta spec **no define todavía su mecanismo de generación**. En particular, no se fija aquí ninguna relación determinista con Activation, ni ningún esquema "probabilístico condicionado" con factores y pesos concretos — eso sería adelantar, desde la spec de datos, un supuesto sobre la relación Activation↔conversión que el diagnóstico debe descubrir, no recibir ya resuelto.

El mecanismo de generación de `converted_to_paid` (sea cual sea su forma final: independiente, condicionado por comportamiento, u otra) se definirá exclusivamente en la etapa posterior de parametrización (sección 17), separada de esta spec de schema y taxonomía. Lo único que esta spec fija es la restricción de principio (sección 1, principio 3): el mecanismo elegido no debe fabricar de antemano la conclusión de que Activation determina conversión.

---

## 10. Registration Abandonment

**Decisión cerrada:** no se genera `registration_abandoned` como evento. El abandono se deriva posteriormente, en la fase de diagnóstico, identificando identidades (`anonymous_id`) que tienen `registration_started` sin `registration_completed` asociado.

La regla temporal para distinguir "abandono" de "todavía en proceso" (el valor X de minutos/horas de inactividad) **no se fija en esta spec** — se definirá en la fase de diagnóstico, como pediste. Esto es coherente con el principio de la sección 1: el generador no necesita saber esa regla para producir los datos crudos; solo necesita que existan identidades con `registration_started` y sin `registration_completed` en proporción realista (proporción que tampoco se fija aquí — ver sección 17).

---

## 11. Casos de comportamiento que el dataset debe poder representar

Checklist de cobertura obligatoria (sin porcentajes todavía):

1. Abandona registro (`registration_started` sin `registration_completed`).
2. Completa registro pero no inicia onboarding.
3. Inicia onboarding y abandona antes de completarlo.
4. Primera acción rápida tras signup.
5. Primera acción tardía tras signup.
6. Conecta fuente pero no crea dashboard.
7. Crea dashboard pero no visualiza insight.
8. Completa First Value ≤ 7 días.
9. Completa First Value > 7 días.
10. Aún no completa First Value (al cierre de la ventana de observación).
11. Convierte a paid.
12. No convierte a paid.

**Verificación de consistencia:** cada uno de estos 12 casos debe ser alcanzable combinando exclusivamente los eventos definidos en la sección 6, sin necesitar ninguna variable derivada almacenada. Esta lista es una prueba de que la taxonomía de eventos es suficiente para todo lo que luego querremos diagnosticar — no es todavía una asignación de cuántos usuarios caen en cada caso.

---

## 12. Distribuciones y realismo

Dimensiones que deben tener variabilidad (sin fijar pesos ni tasas en esta spec):

- País
- Rol
- Industria
- Tamaño de empresa
- Caso de uso
- Canal de adquisición
- Comportamiento temporal (velocidad hacia cada milestone)
- Frecuencia de sesiones
- Features utilizadas

**Regla explícita reforzada (decisión 9 de esta ronda):** ningún rango, tasa de conversión entre etapas del funnel, ni peso de distribución se fija en esta especificación. Esto incluye explícitamente la probabilidad de `converted_to_paid` (sección 9.1) y el volumen de abandono de registro (sección 10). Todos estos parámetros se definirán en una etapa posterior, separada, después de que la taxonomía y las reglas de generación queden completamente cerradas — precisamente para que el generador no fabrique un bottleneck de antemano.

---

## 13. Volumetría y periodo

- **10.000 usuarios** con cuenta creada (`users.csv`) — cifra ya aprobada en `CLAUDE.md`.
- Volumen de identidades pre-account que nunca completan el registro: a definir en la etapa de parámetros (sección 17), no en esta spec.
- Periodo temporal de simulación (rango de fechas de `signup_date`, para observar cohortes distintas en vez de un único instante): a definir en la etapa de parámetros.
- Ventana de observación: debe extenderse lo suficiente después del último `signup_date` generado para que el Late Value (First Value > 7 días) sea observable sin truncamiento artificial — regla de diseño a respetar, valor exacto a definir en parámetros.
- Regla para no generar eventos imposibles: ningún evento con `event_timestamp` posterior a la fecha de corte de la simulación; ningún evento de un usuario con `event_timestamp` anterior a su propio `registration_started`.

---

## 14. Reglas de validación

Checks automáticos que deberán ejecutarse sobre el dataset generado antes de darlo por válido:

1. **Integridad referencial:** todo `user_id` no nulo en `events.csv` existe en `users.csv`.
2. **Cobertura de cuentas:** todo `user_id` en `users.csv` tiene al menos un evento `registration_completed` correspondiente en `events.csv`, con el mismo timestamp que `signup_date`.
3. **Coherencia temporal:** ningún evento precede a `registration_started` de su misma identidad; `registration_completed` no precede a `registration_started`.
4. **Identidad pre/post account:** todo evento con `user_id = null` tiene `anonymous_id` no nulo.
5. **First Value reconstruible:** para una muestra de usuarios, los tres eventos de First Value son atribuibles al mismo `user_id` y sus timestamps son coherentes.
6. **Registration Abandonment reconstruible:** existen identidades con `registration_started` y sin `registration_completed`, en proporción no nula.
7. **Ausencia de variables derivadas prohibidas:** ninguna columna de `users.csv` ni `events.csv` coincide con la lista negada de `CLAUDE.md` §6.
8. **Sin eventos imposibles:** ningún evento posterior a la fecha de corte de la simulación; ningún evento de una familia post-signup con `user_id = null`.
9. **Unicidad:** `user_id` único en `users.csv`; `event_id` único en `events.csv`.
10. **Metadata bien formada:** todo valor de `metadata` es JSON válido (incluyendo `{}` vacío).

---

## 15. Outputs

- `users.csv`
- `events.csv`
- Un archivo auxiliar de parámetros/semillas de generación (p. ej. `generation_params.yaml` o similar), **propuesto pero no confirmado** — su propósito sería exclusivamente de reproducibilidad técnica (semilla aleatoria, versión de la spec usada), no de negocio. Queda como decisión abierta en la sección 17.

---

## 16. Trazabilidad

Cada campo de `users.csv` (sección 3) y cada evento de `events.csv` (sección 6) incluye explícitamente su "pregunta analítica que responde", enlazada a las preguntas numeradas de `01_CONTEXT.md` §6 y del Working Document §38. Ningún campo o evento de esta spec carece de esa referencia.

---

## 17. Separación de capas y decisiones pendientes

Se reafirma la cadena:

```text
OBSERVADO → DERIVADO → DIAGNÓSTICO → DECISIÓN
```

Esta especificación produce exclusivamente la capa **OBSERVADO**. Cualquier mención a Activation, Late Value, Registration Abandonment o conversión a lo largo de este documento existe únicamente para justificar por qué existe un campo o evento — nunca para fijar su valor, su tasa de ocurrencia o su distribución.

### Decisiones que quedan explícitamente pendientes (etapa posterior, separada de esta spec)

1. **Definición final de First Action** (sección 8): qué eventos concretos de la taxonomía cuentan como "primera interacción significativa" — pendiente de revisión conjunta antes de pasar a diagnóstico.
2. **Metadata exacta de `data_source_connected`, `dashboard_created` e `insight_viewed`**: qué propiedades observables se incluyen (tipo de fuente, origen del dashboard, tipo de insight) — a precisar antes de escribir el script generador.
3. **Regla temporal (valor X) para inferir Registration Abandonment** — se define en fase de diagnóstico, no aquí.
4. **Mecanismo de generación de `converted_to_paid`** (si será independiente, condicionado por comportamiento, o de otra forma; y en ese caso, qué factores pesan y cuánto) — etapa de parámetros, con la única restricción ya fijada de no imponer una relación determinista con Activation.
5. **Todas las distribuciones, tasas de conversión entre etapas del funnel, y volumetría de identidades pre-account** (secciones 12-13) — etapa de parámetros, deliberadamente posterior y separada.
6. **Archivo auxiliar de reproducibilidad** (`generation_params.yaml` o similar, sección 15) — confirmar si se incluye.
7. **Si `session_started` debe poder ocurrir con `user_id = null`** para visitantes pre-account que exploran sin registrarse (sección 6.4) — a confirmar, ya que no estaba contemplado explícitamente en las decisiones de esta ronda.
