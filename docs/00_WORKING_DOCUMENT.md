# CloudMetrics — Lifecycle & Automation Marketing Leader
## Documento maestro de contexto, datos, diagnóstico y automatización

> **Propósito de este documento:** servir como fuente única de contexto para que una persona o un agente de IA, sin conocimiento previo del proyecto, pueda entender qué es CloudMetrics, qué queremos investigar, cómo se estructura el dataset, qué significa cada etapa del journey, qué variables son observadas vs. derivadas y qué análisis debe realizarse antes de diseñar el Lifecycle Journey.
>
> **Regla fundamental:** primero observamos el comportamiento real/simulado; después calculamos métricas y estados; luego diagnosticamos; finalmente diseñamos segmentos, journeys y automatizaciones. No debemos diseñar el resultado antes de analizar los datos.

---

# 1. Contexto del reto

La prueba técnica busca diseñar un sistema de Lifecycle Marketing para **CloudMetrics**, una SaaS B2B, que demuestre:

- pensamiento sistémico;
- uso práctico de IA;
- orquestación de herramientas;
- orientación a resultados de negocio;
- liderazgo técnico y estratégico;
- capacidad de convertir datos y comportamiento en decisiones automatizadas.

El reto permite utilizar datos ficticios o simulados y asumir variables adicionales del negocio.

El sistema debe poder conectar:

**datos de usuario + eventos de producto + CRM + canales de comunicación + agentes de IA + automatizaciones + medición.**

El foco elegido para este documento es:

> **Onboarding y Activation**

Pero el análisis comienza **antes de que exista una cuenta**, porque una persona puede iniciar el registro y abandonarlo antes de convertirse en usuario.

---

# 2. Definición de trabajo de CloudMetrics

## 2.1 ¿Qué es CloudMetrics?

Para efectos del caso, CloudMetrics es una plataforma SaaS B2B de analítica empresarial que permite a las empresas:

1. conectar fuentes de datos;
2. construir dashboards;
3. obtener insights para tomar decisiones.

Puede entenderse como una herramienta similar a Power BI en el sentido de que centraliza datos y permite visualizarlos, pero esta es una **definición de trabajo creada para el caso**, no una afirmación sobre una empresa real.

## 2.2 Usuarios

Trabajaremos inicialmente con tres perfiles principales:

- Marketing
- Ventas / Revenue
- Operaciones

## 2.3 Modelo de negocio

CloudMetrics funciona bajo un modelo:

**SaaS B2B → prueba gratuita → suscripción paga.**

## 2.4 Journey general

El journey conceptual completo es:

**Entrada → Registro → Onboarding → Activation → Adoption → Conversión → Retención**

Para este reto nos concentraremos principalmente en:

**Entrada → Registro → Onboarding → Activation**

La conversión a pago se conservará como resultado downstream para analizar posteriormente su relación con Activation.

---

# 3. Pregunta central que queremos resolver

No partimos de un bottleneck conocido.

Queremos utilizar los datos para descubrir:

> **¿En qué punto del journey los nuevos usuarios pierden impulso, qué comportamientos explican esa fricción y qué intervenciones de Lifecycle podrían ayudar a llevarlos más rápidamente al primer momento de valor?**

Esta pregunta contiene dos posibles zonas de fricción:

### A. Registration friction

La persona muestra intención, comienza el proceso de registro, pero abandona antes de crear la cuenta.

### B. Onboarding / activation friction

La persona crea una cuenta, pero no consigue llegar al primer momento de valor, o llega demasiado tarde.

Estas dos situaciones deben analizarse por separado.

**No debemos asumir que todo abandono previo a Activation es un problema de onboarding.**

---

# 4. Principio metodológico: observar primero, calcular después

Esta es una de las decisiones más importantes del proyecto.

## 4.1 Datos observados

Son eventos o atributos que representan algo que realmente ocurrió o que conocemos directamente.

Ejemplos:

- una persona inició el registro;
- completó un campo;
- abandonó el formulario;
- creó una cuenta;
- inició onboarding;
- conectó una fuente;
- creó un dashboard;
- visualizó un insight;
- utilizó una feature;
- convirtió a pago.

## 4.2 Variables derivadas

Son conclusiones, estados o métricas que calculamos posteriormente a partir de los datos observados.

Ejemplos:

- `registration_abandonment`
- `registration_completion_rate`
- `first_action_timestamp`
- `time_to_first_action`
- `activation_status`
- `first_value_date`
- `days_to_first_value`
- `activation_rate`
- `late_value_rate`
- segmentos comportamentales
- señales tempranas de Activation
- bloqueos/fricciones

### Regla

**Nunca debemos incluir una interpretación como si fuera un evento observado.**

Primero:

```text
Events
↓
Analysis
↓
Derived metrics / states
↓
Diagnosis
↓
Lifecycle strategy
```

---

# 5. Modelo conceptual del journey

El journey debe entenderse como una secuencia de estados observables, no como etiquetas preexistentes.

```text
VISITANTE
   ↓
REGISTRO INICIADO
   ↓
¿COMPLETÓ REGISTRO?
   ├── NO → Registro abandonado
   └── SÍ
        ↓
      CUENTA CREADA
        ↓
      ONBOARDING
        ↓
      MILESTONES DE VALOR
        ↓
      FIRST VALUE
        ↓
      ¿OCURRIÓ DENTRO DE 7 DÍAS?
        ├── SÍ → ACTIVATED
        └── NO → LATE VALUE
```

Si nunca completa los milestones:

```text
Cuenta creada
   ↓
No alcanza First Value
   ↓
NOT ACTIVATED
```

---

# 6. Distinción fundamental: First Value vs. Activation

Esta distinción queda cerrada.

## 6.1 First Value

**First Value** representa el momento en que el usuario experimenta por primera vez el valor central definido para este caso.

Un usuario alcanza First Value cuando completa la secuencia:

1. conecta al menos una fuente de datos;
2. crea su primer dashboard;
3. visualiza su primer insight accionable.

Por tanto:

> **First Value = data source connected + first dashboard created + first actionable insight viewed.**

La fecha/hora en que se completa esta secuencia será:

`first_value_date`

### Importante

First Value **no depende de la ventana de 7 días**.

Si un usuario completa la secuencia en el día 12, igualmente alcanzó First Value.

---

# 7. Activation

Activation es una clasificación temporal basada en First Value.

Definición:

> **Activation = alcanzar First Value dentro de los primeros 7 días desde `signup_date`.**

Por tanto:

```text
First Value ≤ 7 días
        ↓
Activated
```

Mientras que:

```text
First Value > 7 días
        ↓
Late Value
```

Y:

```text
No First Value
        ↓
Not Activated
```

## 7.1 ¿Por qué necesitamos esta distinción?

Porque no queremos cometer el error de decir:

> "Si no se activó en 7 días, nunca recibió valor."

Eso sería falso.

Un usuario puede tardar 12 días y finalmente experimentar el valor.

Por eso conservaremos ambos conceptos:

### First Value

**¿Alguna vez llegó al valor definido?**

### Activation

**¿Llegó a ese valor dentro de la ventana crítica de 7 días?**

---

# 8. Estados derivados de valor

Para el análisis podemos utilizar:

| Estado | Definición |
|---|---|
| `not_activated` | Todavía no alcanza First Value |
| `activated` | Alcanza First Value ≤ 7 días |
| `late_value` | Alcanza First Value > 7 días |

Estos estados **no estarán almacenados originalmente en `users.csv`**.

Serán calculados a partir de `events.csv`.

---

# 9. Ejemplo de usuarios

| Usuario | Fuente | Dashboard | Insight | Día de First Value | Estado |
|---|---:|---:|---:|---:|---|
| U001 | ✓ | ✓ | ✓ | 3 | Activated |
| U002 | ✓ | ✓ | ✓ | 6 | Activated |
| U003 | ✓ | ✓ | ✓ | 12 | Late Value |
| U004 | ✓ | ✓ | ✓ | 30 | Late Value |
| U005 | ✓ | ✓ | ✗ | — | Not Activated |

Esto nos permite analizar algo más interesante que simplemente "activado vs. no activado".

Podremos estudiar:

> **¿Qué comportamientos tempranos diferencian a quienes llegan rápido al valor, quienes llegan tarde y quienes nunca llegan?**

---

# 10. Métricas principales

## 10.1 Activation Rate

Porcentaje de usuarios que alcanzan First Value dentro de los primeros 7 días.

```text
Activated users
---------------------------- × 100
Users with account created
```

## 10.2 First Value Rate

Porcentaje de usuarios que eventualmente alcanzan First Value, independientemente del tiempo.

```text
Users who reached First Value
---------------------------- × 100
Users with account created
```

## 10.3 Late Value Rate

Porcentaje de usuarios que alcanzan First Value después del día 7.

```text
Late Value users
---------------------------- × 100
Users with account created
```

## 10.4 Non-Value Rate

Porcentaje de usuarios que todavía no alcanzaron First Value.

```text
Users without First Value
---------------------------- × 100
Users with account created
```

## 10.5 Time to First Value

Tiempo entre:

`signup_date`

y

`first_value_date`

```text
Time to First Value =
first_value_date − signup_date
```

## 10.6 Time to First Action

Tiempo entre:

`signup_date`

y

`first_action_timestamp`

---

# 11. ¿Qué cuenta como First Action?

`first_action_timestamp` será una variable derivada.

Definición:

> **Primera interacción significativa con el producto después del registro.**

El signup no cuenta como acción.

Ejemplo:

| user_id | signup | first_action |
|---|---|---|
| U001 | 09:00 | 09:04 |
| U002 | 10:30 | 11:15 |
| U003 | 14:00 | 16:42 |

Después calculamos:

```text
Time to First Action =
first_action_timestamp − signup_date
```

Esto nos permitirá investigar si una interacción temprana está asociada con una mayor probabilidad de Activation.

---

# 12. `users.csv`: schema definitivo

`users.csv` representa exclusivamente personas que **completaron el registro y tienen una cuenta creada**.

Una persona que inicia el formulario pero abandona antes de crear la cuenta **no aparecerá en `users.csv`**.

Su comportamiento pre-account se conservará en `events.csv`.

## 12.1 Campos

| Campo | Tipo | Ejemplo | Observado / derivado | Definición |
|---|---|---|---|---|
| `user_id` | string | U001234 | Observado | Identificador único de la cuenta |
| `first_name` | string | María | Observado | Nombre registrado |
| `last_name` | string | Gómez | Observado | Apellido registrado |
| `email` | string | maria@empresa.com | Observado | Email asociado |
| `country` | string | Colombia | Observado | País declarado |
| `signup_date` | datetime | 2026-08-01 09:32:14 | Observado | Momento en que se crea la cuenta |
| `role` | string | Marketing Manager | Observado | Rol declarado |
| `industry` | string | SaaS | Observado | Industria declarada |
| `company_size` | string | 51–200 | Observado | Tamaño de empresa |
| `use_case` | string | Marketing Analytics | Observado | Caso de uso declarado |
| `acquisition_channel` | string | Organic Search | Observado | Canal de adquisición |
| `converted_to_paid` | boolean/integer | 0 | Observado / resultado downstream | Si posteriormente convirtió a pago |

## 12.2 Campos que NO estarán en `users.csv`

No incluiremos:

- `lifecycle_stage`
- `first_action_timestamp`
- `time_to_first_action`
- `onboarding_status`
- `activation_status`
- `first_value_date`
- `days_to_first_value`
- `activation_score`
- `registration_abandonment`

Todos estos serán derivados a partir de eventos o análisis.

---

# 13. Definición de `signup_date`

`signup_date` representa el momento exacto en que la persona completa el registro y se crea su cuenta.

Ejemplo:

> María entra a CloudMetrics → completa nombre, email, empresa, rol, etc. → hace clic en "Crear cuenta" → `signup_date = 2026-08-01 09:32:14`.

Este timestamp representa el **inicio del reloj de Lifecycle para usuarios con cuenta creada**.

---

# 14. `events.csv`: schema definitivo

`events.csv` es la fuente principal para reconstruir el comportamiento.

Puede contener eventos de:

- personas que todavía no tienen cuenta;
- usuarios con cuenta;
- usuarios activados;
- usuarios que llegan tarde al valor.

## 14.1 Campos

| Campo | Tipo | Ejemplo | Definición |
|---|---|---|---|
| `event_id` | string | E000001 | Identificador único del evento |
| `event_timestamp` | datetime | 2026-08-01 09:28:41 | Momento exacto del evento |
| `event_name` | string | signup_started | Evento estandarizado |
| `user_id` | string / null | U001234 / null | ID de cuenta; null si aún no existe |
| `anonymous_id` | string | A8F92K | Identificador persistente antes de crear cuenta |
| `session_id` | string | S9D21X | Identificador de sesión |
| `source` | string | web | Superficie donde ocurrió |
| `metadata` | JSON | `{"feature":"filters"}` | Contexto específico del evento |

---

# 15. Identidad antes y después del registro

Antes de crear una cuenta:

```text
user_id = null
anonymous_id = A8F92K
session_id = S9D21X
```

Después de completar el registro:

```text
user_id = U001234
anonymous_id = A8F92K
session_id = S9D21X
```

Esto permite conectar el comportamiento pre-account con la cuenta creada cuando la simulación lo permita.

No debemos asumir que todos los visitantes abandonados pueden identificarse personalmente.

---

# 16. Taxonomía definitiva de eventos

La regla es:

> **Cada evento debe existir porque responde una pregunta concreta del journey.**

## 16.1 Entrada y registro

| Evento | user_id | Propósito |
|---|---|---|
| `landing_viewed` | null | Detectar entrada al sitio/producto |
| `signup_started` | null | Detectar intención de registro |
| `signup_form_started` | null | Detectar interacción real con el formulario |
| `signup_form_field_completed` | null | Analizar progreso y posibles puntos de fricción |
| `signup_abandoned` | null | Registrar abandono del proceso |
| `signup_completed` | nuevo user_id | Marcar creación de cuenta |

### Metadata de `signup_form_field_completed`

Ejemplo:

```json
{
  "field": "company_size"
}
```

Esto permite investigar si determinados campos presentan una caída desproporcionada.

---

# 17. Regla para `signup_abandoned`

No debemos considerar abandono simplemente porque una persona dejó de interactuar durante unos segundos.

Para el dataset simulado utilizaremos una regla temporal explícita:

```text
signup_form_started
+
no signup_completed
+
ausencia de actividad durante X minutos
=
signup_abandoned
```

El valor de **X** deberá definirse antes de generar los datos y mantenerse constante durante toda la simulación.

Esta regla es importante porque `signup_abandoned` es una **variable inferida**, aunque pueda representarse como evento derivado en el dataset analítico.

---

# 18. Eventos de onboarding

| Evento | Propósito |
|---|---|
| `onboarding_started` | Indica inicio de configuración |
| `profile_completed` | Indica finalización de configuración requerida |
| `onboarding_completed` | Indica finalización del onboarding |

---

# 19. Eventos de First Value

Estos son los tres milestones que constituyen la definición operacional de First Value:

| Evento | Propósito |
|---|---|
| `data_source_connected` | Conectar al menos una fuente |
| `dashboard_created` | Crear el primer dashboard |
| `insight_viewed` | Visualizar el primer insight accionable |

La secuencia esperada es:

```text
data_source_connected
        ↓
dashboard_created
        ↓
insight_viewed
```

Sin embargo, el análisis deberá observar los eventos reales y no asumir que siempre ocurren perfectamente en ese orden.

---

# 20. ¿Cómo calculamos `first_value_date`?

Para cada usuario:

1. identificar su primer `data_source_connected`;
2. identificar su primer `dashboard_created`;
3. identificar el primer `insight_viewed` que complete la condición de First Value;
4. verificar que los tres milestones puedan atribuirse al mismo usuario;
5. tomar como `first_value_date` el timestamp del evento que completa la secuencia.

Ejemplo:

```text
Aug 1 09:10 → data_source_connected
Aug 1 09:25 → dashboard_created
Aug 3 10:15 → insight_viewed
                     ↓
             first_value_date
```

Entonces:

```text
days_to_first_value ≈ 2 días
activation_status = activated
```

---

# 21. ¿Qué pasa si completa First Value después de 7 días?

No se pierde el dato.

Ejemplo:

```text
Signup:       Aug 1
Data source:  Aug 3
Dashboard:    Aug 8
Insight:      Aug 12
```

El usuario **sí alcanzó First Value**, pero:

```text
days_to_first_value > 7
```

Por tanto:

```text
first_value_status = reached
activation_status = late_value
```

Esto permite diferenciar:

### Activated

Llegó al valor dentro de la ventana crítica.

### Late Value

Llegó al valor, pero demasiado tarde para considerarlo Activation dentro del período definido.

### Not Activated

Todavía no llegó al valor.

---

# 22. Comportamiento y adopción posterior

| Evento | Propósito |
|---|---|
| `session_started` | Medir recurrencia y continuidad |
| `dashboard_viewed` | Analizar consumo |
| `feature_used` | Analizar adopción |
| `dashboard_shared` | Identificar colaboración y expansión |

`feature_used` conservará metadata.

Ejemplo:

```json
{
  "feature": "filters"
}
```

o:

```json
{
  "feature": "sharing"
}
```

No utilizaremos inicialmente:

```text
features_used = 5
```

porque perderíamos la secuencia y contexto.

---

# 23. Funnel analítico definitivo

El funnel que debemos analizar será:

```text
Landing viewed
      ↓
Signup started
      ↓
Signup form started
      ↓
Form progress
      ↓
Signup completed
      ↓
Onboarding started
      ↓
Onboarding completed
      ↓
Data source connected
      ↓
Dashboard created
      ↓
Insight viewed
      ↓
First Value
      ↓
┌──────────────────────────────┐
│ ¿First Value ≤ 7 días?       │
└──────────────────────────────┘
       ↓             ↓
      SÍ             NO
       ↓             ↓
 ACTIVATED       LATE VALUE
```

Y existe una tercera rama:

```text
No First Value
      ↓
NOT ACTIVATED
```

---

# 24. Dos embudos que NO debemos mezclar

## Funnel 1 — Registration

```text
Landing
↓
Signup Started
↓
Form Started
↓
Form Progress
↓
Signup Completed
```

Objetivo:

> detectar fricción antes de crear la cuenta.

## Funnel 2 — Onboarding / Activation

```text
Signup Completed
↓
Onboarding Started
↓
Onboarding Completed
↓
Data Source Connected
↓
Dashboard Created
↓
Insight Viewed
↓
First Value
```

Objetivo:

> reducir el tiempo y aumentar la probabilidad de llegar al primer valor.

Esto evita diseñar una única intervención para problemas completamente diferentes.

---

# 25. Análisis que deberá realizarse después de generar los datos

Todavía **no conocemos** cuál será el bottleneck.

El diagnóstico deberá responder:

## Registration

- ¿Qué porcentaje inicia registro?
- ¿Qué porcentaje completa registro?
- ¿Dónde se concentra el abandono?
- ¿Qué campos generan mayor fricción?
- ¿Cuánto tarda la gente en completar el formulario?
- ¿Qué canales presentan mayor abandono?
- ¿Existen diferencias por perfil?

## Onboarding

- ¿Qué porcentaje inicia onboarding?
- ¿Qué porcentaje lo completa?
- ¿Dónde ocurre la mayor caída?
- ¿Cuánto tiempo transcurre entre registro y primera acción?
- ¿Qué comportamientos tempranos diferencian a los usuarios?

## First Value

- ¿Qué porcentaje alcanza First Value?
- ¿Qué porcentaje lo alcanza dentro de 7 días?
- ¿Qué porcentaje lo alcanza después?
- ¿Cuánto tarda en promedio/mediana?
- ¿Qué milestone presenta mayor fricción?

## Activation

- ¿Qué comportamientos predicen Activation?
- ¿Qué comportamientos predicen Late Value?
- ¿Qué comportamientos aparecen en quienes nunca llegan a First Value?

## Downstream

- ¿Activation está asociada con mayor conversión a pago?
- ¿Late Value tiene comportamiento diferente?
- ¿La velocidad hacia First Value se relaciona con conversión?

---

# 26. Variables derivadas principales

A partir de `users.csv` + `events.csv` podremos calcular:

### Registration

- `registration_completion_status`
- `registration_abandonment`
- `registration_time_to_complete`
- `signup_form_completion_rate`

### Onboarding

- `onboarding_status`
- `onboarding_completion_time`

### Early behavior

- `first_action_timestamp`
- `time_to_first_action`

### Value

- `first_value_date`
- `days_to_first_value`
- `first_value_status`

### Activation

- `activation_status`
- `activation_rate`
- `late_value_rate`
- `non_value_rate`

### Behavioral diagnosis

- conversion entre milestones;
- secuencias frecuentes;
- señales tempranas;
- segmentos comportamentales;
- bloqueos/fricciones.

---

# 27. No generar variables interpretativas artificialmente

No generaremos inicialmente:

- `lifecycle_stage`
- `activation_score`
- `activation_status`
- `first_value_date`
- `days_to_first_value`
- `first_action_timestamp`
- `registration_abandonment`

como columnas predeterminadas de los usuarios.

La lógica será:

```text
USERS + EVENTS
       ↓
     QUERY
       ↓
  CALCULATIONS
       ↓
 DERIVED STATES
       ↓
  DIAGNOSTIC
```

Esto hace que la solución sea técnicamente defendible.

---

# 28. `converted_to_paid`

`converted_to_paid` sí permanecerá en `users.csv`.

Es un resultado downstream.

Nos permitirá investigar:

> ¿Los usuarios que llegan rápidamente al valor tienen mayor probabilidad de convertir a pago?

Pero **no se utilizará para definir Activation**.

El análisis causal no se asumirá automáticamente. Una correlación entre Activation y pago será una señal para investigar, no una prueba de causalidad.

---

# 29. Principio de generación de los datos simulados

No debemos diseñar los datos para confirmar de antemano la solución.

Los 10.000 usuarios deben permitir descubrir:

- personas que nunca comienzan registro;
- personas que comienzan pero abandonan;
- personas que completan registro;
- usuarios que abandonan onboarding;
- usuarios que conectan datos pero no crean dashboard;
- usuarios que crean dashboard pero no visualizan insight;
- usuarios que alcanzan First Value rápidamente;
- usuarios que alcanzan First Value tarde;
- usuarios que nunca alcanzan First Value;
- usuarios que convierten a pago;
- usuarios que no convierten.

El bottleneck y los segmentos prioritarios serán **resultado del análisis**, no una premisa.

---

# 30. Principio de diseño del Lifecycle

Una vez identificado el bottleneck:

```text
Behavior
   ↓
Diagnosis
   ↓
Segment
   ↓
Blocker
   ↓
Next Best Action
   ↓
Channel
   ↓
Message
   ↓
Timing
   ↓
Outcome
```

No queremos un journey genérico como:

```text
Día 1 → Email
Día 3 → Email
Día 5 → WhatsApp
```

Queremos lógica condicional basada en comportamiento.

Ejemplo conceptual:

```text
Usuario en día 3
+
Fuente conectada
+
Dashboard no creado
        ↓
AI Decision Agent
        ↓
Necesidad: ayuda para construir primer dashboard
        ↓
Intervención específica
```

Mientras que:

```text
Usuario en día 3
+
No inició onboarding
        ↓
Necesidad diferente
        ↓
Intervención diferente
```

---

# 31. Implicación para el AI Decision Agent

La IA no debe limitarse a escribir mensajes.

Debe ayudar a decidir:

> **qué necesita este usuario ahora y cuál es la siguiente mejor acción.**

## Inputs potenciales

- perfil del usuario;
- acquisition channel;
- eventos recientes;
- tiempo desde signup;
- último milestone alcanzado;
- estado derivado del funnel;
- First Value status;
- historial de intervenciones;
- respuesta a intervenciones anteriores.

## Output conceptual

```text
User state
↓
Detected blocker
↓
Next Best Action
↓
Channel
↓
Timing
↓
Message / intervention
↓
Expected outcome
```

## Caso pre-account

Para alguien que abandonó el registro:

```text
Signup progress
+
Last completed field
+
Time since abandonment
+
Acquisition channel
        ↓
AI Decision Agent
        ↓
¿Vale la pena recuperar?
        ↓
Canal + intervención
```

## Caso post-account

```text
Recent events
+
Current milestone
+
Days since signup
+
First Value progress
        ↓
AI Decision Agent
        ↓
Blocker
        ↓
Next Best Action
```

---

# 32. Límites del AI Agent

El agente no deberá:

- inventar eventos;
- modificar el estado real del usuario;
- declarar Activation sin evidencia;
- asumir que no alcanzar Activation equivale a no haber recibido valor;
- utilizar `converted_to_paid` para decidir si alguien está activado;
- enviar comunicaciones sin respetar las condiciones de entrada/salida;
- reemplazar las reglas determinísticas cuando una regla simple sea suficiente.

La IA se utilizará donde aporte valor real a la decisión.

---

# 33. Arquitectura conceptual del sistema

```text
             ┌──────────────────────┐
             │ Acquisition / Web    │
             └──────────┬───────────┘
                        ↓
                Pre-account events
                        ↓
             ┌──────────────────────┐
             │ Registration funnel  │
             └──────────┬───────────┘
                        ↓
                 Account created
                        ↓
                 users.csv
                        +
                 events.csv
                        ↓
              Behavioral analysis
                        ↓
              Derived user state
                        ↓
              AI Decision Agent
                        ↓
                Next Best Action
                        ↓
             Email / WhatsApp / SMS
                        ↓
                 User behavior
                        ↓
                  Measurement
                        ↓
                   Learning
```

---

# 34. KPIs del sistema

## KPI principal

**Activation Rate**

Porcentaje de nuevos usuarios que alcanzan First Value dentro de los primeros 7 días.

## KPIs secundarios

### Registration

- Signup completion rate
- Registration abandonment rate
- Form completion rate
- Time to registration

### Onboarding

- Onboarding completion rate
- Milestone conversion
- Time to First Action

### Value

- First Value Rate
- Activation Rate
- Late Value Rate
- Non-Value Rate
- Time to First Value

### Business

- Trial → Paid conversion
- Retention
- Feature adoption

---

# 35. Cómo distinguir mejora real de variación normal

La prueba técnica pide pensar en cómo validar hipótesis antes de escalar.

Por tanto, las intervenciones deberán evaluarse con:

- grupos de control;
- experimentos A/B cuando sea posible;
- comparación de cohortes;
- métricas de funnel;
- tiempo suficiente para observar comportamiento;
- análisis por segmentos.

No debemos medir únicamente:

> "¿Abrieron el email?"

La métrica final debe conectarse con el comportamiento objetivo:

```text
Intervention
↓
Milestone completion
↓
First Value
↓
Activation
↓
Paid conversion / retention
```

---

# 36. Orden de trabajo

No debemos diseñar el journey final antes de ejecutar el diagnóstico.

El orden correcto es:

### Fase 1 — Data

1. Definir schema.
2. Generar datos simulados.
3. Validar consistencia temporal.
4. Validar identidad pre-account → account.

### Fase 2 — Diagnosis

5. Analizar registration funnel.
6. Analizar onboarding funnel.
7. Analizar First Value.
8. Analizar Activation vs. Late Value vs. Not Activated.
9. Identificar bottleneck.
10. Identificar señales tempranas.
11. Identificar segmentos.

### Fase 3 — Strategy

12. Definir segmentos prioritarios.
13. Definir bloqueos.
14. Definir Next Best Actions.
15. Definir journeys.
16. Definir canales.
17. Definir condiciones de entrada/salida.

### Fase 4 — AI

18. Definir AI Decision Agent.
19. Definir inputs.
20. Definir lógica.
21. Definir prompt.
22. Definir outputs.
23. Definir límites.

### Fase 5 — Measurement

24. Definir experimentación.
25. Definir KPIs.
26. Definir control groups.
27. Definir aprendizaje continuo.

---

# 37. Decisiones metodológicas cerradas

| Tema | Decisión |
|---|---|
| Foco | Onboarding + Activation |
| Pre-account behavior | Sí se captura |
| `users.csv` | Solo cuentas creadas |
| `events.csv` | Pre-account + post-account |
| `user_id` pre-account | Null |
| Identidad pre-account | `anonymous_id` + `session_id` |
| `lifecycle_stage` | Variable derivada, no inicial |
| `converted_to_paid` | Sí, como resultado downstream |
| `first_action_timestamp` | Derivada de eventos |
| First Value | Conectar fuente + crear dashboard + visualizar primer insight accionable |
| `first_value_date` | Momento en que se completa First Value |
| Activation | First Value ≤ 7 días |
| Late Value | First Value > 7 días |
| Not Activated | No alcanza First Value |
| `days_to_first_value` | `first_value_date - signup_date` |
| `activation_score` | No se define inicialmente |
| `signup_abandoned` | Inferido mediante regla temporal explícita |
| `feature_used` | Incluye metadata de feature |
| Bottleneck | No se asume; se descubre mediante análisis |
| Journey | Se diseña después del diagnóstico |
| AI | Decide Next Best Action; no solo genera copy |

---

# 38. Preguntas que el diagnóstico debe responder

Antes de diseñar cualquier automatización, debemos poder responder:

1. ¿Cuánta gente entra al funnel?
2. ¿Cuánta empieza el registro?
3. ¿Cuánta abandona antes de crear una cuenta?
4. ¿Dónde abandonan?
5. ¿Quiénes tienen mayor probabilidad de abandonar?
6. ¿Qué porcentaje de cuentas inicia onboarding?
7. ¿Dónde se rompe el onboarding?
8. ¿Cuál es el primer milestone que mejor predice First Value?
9. ¿Qué porcentaje alcanza First Value?
10. ¿Qué porcentaje alcanza First Value dentro de 7 días?
11. ¿Qué porcentaje llega tarde?
12. ¿Qué porcentaje nunca llega?
13. ¿Qué comportamientos tempranos predicen Activation?
14. ¿Qué comportamientos predicen Late Value?
15. ¿Qué comportamientos predicen no llegar a First Value?
16. ¿Qué segmentos presentan bloqueos diferentes?
17. ¿Activation está asociada con mayor conversión a pago?
18. ¿Cuál es la intervención de mayor potencial?
19. ¿Qué debe decidir el AI Agent?
20. ¿Cómo mediremos si la intervención realmente funciona?

---

# 39. Estado actual del proyecto

Las siguientes definiciones están cerradas:

- CloudMetrics = SaaS B2B de analítica.
- Foco = Onboarding + Activation.
- Registration friction se analiza por separado.
- `users.csv` contiene solo cuentas creadas.
- `events.csv` contiene comportamiento pre-account y post-account.
- First Value = conectar fuente + crear dashboard + visualizar insight accionable.
- Activation = First Value dentro de 7 días.
- First Value después de 7 días = Late Value, no "nunca activado".
- No First Value = Not Activated.
- Las métricas y estados se derivan después de observar los eventos.
- El bottleneck todavía no está definido.
- El journey final todavía no está definido.
- El AI Agent todavía no tiene lógica final.
- El siguiente paso es generar y analizar el dataset.

---

# 40. Regla final para cualquier persona o IA que continúe este proyecto

Si una persona o agente de IA recibe este documento sin ningún otro contexto, debe seguir estas reglas:

### Regla 1
**No asumir cuál es el bottleneck.**

### Regla 2
**No confundir registro abandonado con onboarding abandonado.**

### Regla 3
**No confundir First Value con Activation.**

First Value responde:

> "¿Alguna vez experimentó el valor definido?"

Activation responde:

> "¿Experimentó ese valor dentro de los primeros 7 días?"

### Regla 4
**No clasificar como "no activado" a alguien que alcanzó First Value después del día 7.**

Debe clasificarse como `late_value`.

### Regla 5
**No crear variables derivadas antes de observar los eventos.**

### Regla 6
**No diseñar el Lifecycle Journey antes del diagnóstico.**

### Regla 7
**No utilizar IA solo para escribir mensajes.**

La IA debe ayudar a tomar decisiones de Lifecycle cuando exista una decisión que justifique su uso.

### Regla 8
**Toda intervención debe tener una hipótesis, una condición de entrada, una lógica basada en comportamiento, una condición de salida y una métrica de éxito.**

### Regla 9
**El objetivo no es enviar más comunicaciones.**

El objetivo es:

> **reducir fricción, acelerar el Time to First Value, aumentar Activation y generar impacto de negocio.**

### Regla 10

El proceso completo es:

```text
OBSERVE
   ↓
CALCULATE
   ↓
DIAGNOSE
   ↓
SEGMENT
   ↓
DECIDE
   ↓
INTERVENE
   ↓
MEASURE
   ↓
LEARN
```

Ese orden debe mantenerse durante todo el desarrollo del caso.
