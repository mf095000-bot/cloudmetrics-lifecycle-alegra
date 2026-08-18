# 03_SIMULATION_PARAMETERS.md — Universo simulado y catálogos de dimensiones

## 0. Relación con otros documentos

Este documento **no rediseña metodología**. Traduce a parámetros concretos lo ya cerrado en `CLAUDE.md`, `docs/00_WORKING_DOCUMENT.md`, `docs/01_CONTEXT.md` y `docs/02_DATA_GENERATION_SPEC.md`, y define únicamente lo que faltaba para poder generar: el universo temporal/volumétrico y los catálogos de valores de `users.csv`.

No se definen aquí: modelos matemáticos, distribuciones estadísticas, pesos de conversión, semilla, estrategia de sampling, tasas numéricas de las seis transiciones del funnel, ni ninguna definición protegida (First Value, Activation, Late Value, Not Activated). Todo eso permanece exactamente como está en los documentos ya aprobados.

---

## 1. Universo y periodo

| Parámetro | Definición |
|---|---|
| Cuentas completadas (`users.csv`) | 10.000 |
| Cohorte de signup | `registration_completed` entre `2026-07-01 00:00:00` y `2026-07-31 23:59:59` |
| Distribución de `signup_date` | Dentro de julio de 2026 (implementación técnica, sección 5) |
| Eventos posteriores al signup | Pueden ocurrir después del 31 de julio de 2026, según sea necesario para observar First Value rápido, tardío, o su ausencia |
| Población pre-account (identidades que nunca completan registro) | Existe en `events.csv`, tamaño resuelto como decisión técnica en la fase de implementación (sección 5) |

Esto es consistente con `signup_date` como inicio del reloj de Lifecycle (`01_CONTEXT.md` §9) y con la regla de que los usuarios que abandonan el registro no forman parte de las 10.000 cuentas de `users.csv`, aunque su comportamiento pre-account sí exista en `events.csv` (`01_CONTEXT.md` §8, `02_DATA_GENERATION_SPEC.md` §2).

---

## 2. Dimensiones de `users.csv` — catálogos cerrados

Estos catálogos permiten que el diagnóstico posterior cruce **quién es** (estas dimensiones) con **qué hace** (`events.csv`) y **qué resultado obtiene** (estados derivados), tal como establece el Working Document (§4, §12, §29).

### 2.1 `country`

Catálogo cerrado de 14 países de Latinoamérica. Valor estandarizado en inglés para `users.csv`:

| País | Valor en `users.csv` |
|---|---|
| México | `Mexico` |
| Brasil | `Brazil` |
| Colombia | `Colombia` |
| Argentina | `Argentina` |
| Perú | `Peru` |
| Chile | `Chile` |
| Venezuela | `Venezuela` |
| Ecuador | `Ecuador` |
| Bolivia | `Bolivia` |
| Guatemala | `Guatemala` |
| República Dominicana | `Dominican Republic` |
| Honduras | `Honduras` |
| Paraguay | `Paraguay` |
| Uruguay | `Uruguay` |

### 2.2 `role`

Catálogo cerrado de 15 roles, cubriendo perfiles funcionales, analíticos y ejecutivos:

`Marketing Manager`, `Marketing Director`, `Growth Manager`, `Growth Director`, `Product Manager`, `Product Director`, `Data Analyst`, `Business Analyst`, `BI Analyst`, `Data Scientist`, `Sales Manager`, `Sales Director`, `Operations Manager`, `Operations Director`, `Founder / CEO`.

### 2.3 `industry`

Catálogo cerrado de 14 industrias:

`SaaS / Software`, `Financial Services`, `Healthcare`, `Retail / E-commerce`, `Education`, `Professional Services`, `Manufacturing`, `Telecommunications`, `Media / Entertainment`, `Travel / Hospitality`, `Logistics / Transportation`, `Real Estate`, `Consumer Goods`, `Other`.

### 2.4 `company_size`

Catálogo cerrado de 7 rangos estándar:

`1-10`, `11-50`, `51-200`, `201-500`, `501-1000`, `1001-5000`, `5001+`.

### 2.5 `use_case`

Catálogo cerrado de 10 casos de uso. Representa para qué la cuenta declara que quiere usar el producto — no el comportamiento posterior dentro del producto:

`Marketing Analytics`, `Sales Analytics`, `Product Analytics`, `Customer Analytics`, `Operations Analytics`, `Financial Analytics`, `Executive Reporting`, `Business Intelligence`, `Performance Monitoring`, `Data Exploration`.

### 2.6 `acquisition_channel`

Catálogo cerrado de 10 canales:

`Organic Search`, `Paid Search`, `Paid Social`, `Organic Social`, `Referral`, `Direct`, `Partner`, `Content`, `Email`, `Event / Webinar`.

---

## 3. Reglas de generación para estas dimensiones

- Estas seis dimensiones tendrán **variabilidad real** en el dataset generado — ninguna se reduce a un valor dominante artificial ni a una distribución uniforme forzada.
- Ninguna de estas dimensiones se utilizará para fabricar segmentos "ganadores" o "perdedores". No se declara de antemano que un país, industria, rol, tamaño de empresa, caso de uso o canal tenga mejor o peor Activation, First Value o conversión a pago.
- El bottleneck del funnel no se conoce de antemano y no se diseña a través de estas dimensiones.
- El diagnóstico posterior (fase 4 de `CLAUDE.md`) analizará estas dimensiones junto con los eventos de `events.csv` y los estados derivados (First Value, Activation, Late Value, Not Activated, `converted_to_paid`), habilitando el marco quién→qué hace→qué resultado ya establecido en el Working Document.
- Cualquier relación observada entre estas dimensiones y Activation o conversión a pago **debe surgir de los datos simulados y ser investigada en el diagnóstico**, no estar declarada como verdad de antemano en este documento ni en la implementación del generador.

---

## 4. Reglas ya cerradas que este documento hereda sin modificar

Referencia, no redefinición:

- **Las seis transiciones del funnel** (`registration_started→registration_completed`, `registration_completed→onboarding_started`, `onboarding_started→onboarding_completed`, `onboarding_completed→data_source_connected`, `data_source_connected→dashboard_created`, `dashboard_created→insight_viewed`) se generan respetando los límites de plausibilidad cualitativos ya acordados (abandono real de registro sin dominar el funnel; pérdida baja entre signup y onboarding por ser continuación inmediata; fricción de onboarding sin convertirlo en bottleneck predeterminado; fricción técnica plausible al conectar fuente sin asumir que es el bottleneck; variabilidad suficiente entre conectar fuente y crear dashboard; `insight_viewed` como consumo real de un insight, no apertura del dashboard). Sin tasas numéricas fijadas en este documento.
- **Time-to-Value:** el dataset garantiza usuarios con First Value rápido, tardío (>7 días) y ausente, con los tres grupos de tamaño no trivial. Sin técnica matemática fijada aquí.
- **`converted_to_paid`:** observado/downstream, sin construir la respuesta a si se asocia con Activation (`00_WORKING_DOCUMENT.md` §28, `02_DATA_GENERATION_SPEC.md` §9.1).
- **Variables derivadas** (`lifecycle_stage`, `first_value_date`, `days_to_first_value`, `activation_status`, `activation_score`, `first_action_timestamp`): no se generan como columnas de `users.csv` ni `events.csv`; se calculan posteriormente a partir de USERS + EVENTS.

---

## 5. Decisiones técnicas que se resuelven en la fase de implementación

Estas no son decisiones de negocio pendientes de tu aprobación — son detalles técnicos de cómo el generador cumple lo ya definido. Se resolverán de forma coherente con los documentos existentes y quedarán documentados como decisión técnica en el momento de generar, sin volver a esta conversación:

1. Tamaño exacto de la población pre-account.
2. Distribución exacta de `signup_date` dentro de julio de 2026, y cuánto se extiende la ventana de observación de eventos posteriores.
3. Semilla aleatoria y mecanismo de reproducibilidad.
4. Forma matemática concreta de las distribuciones (funnel, tiempo hasta cada milestone, repeticiones de eventos).
5. Metadata exacta de `data_source_connected` y `dashboard_created` (ya señalada como pendiente en `02_DATA_GENERATION_SPEC.md` §6.3).
6. Detalle operacional de qué distingue `insight_viewed` de simplemente abrir el dashboard, dentro del contrato ya cerrado de la taxonomía de eventos.
7. Pesos de distribución entre valores dentro de cada catálogo de la sección 2 (p. ej. qué proporción de usuarios cae en cada país).

Ninguna de estas decisiones técnicas puede contradecir las definiciones protegidas, las reglas de `CLAUDE.md`, ni las restricciones anti-fabricación ya acordadas.
