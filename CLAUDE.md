# CLAUDE.md — CloudMetrics Lifecycle & Automation Marketing

Este archivo es el contrato de trabajo del proyecto. Rige todas las sesiones de Claude Code sobre este repositorio, incluidas las que no tengan memoria de conversaciones previas.

## 1. Propósito del proyecto

Construir progresivamente, de forma basada en datos, un sistema de Lifecycle & Automation Marketing para **CloudMetrics**, una SaaS B2B de analítica empresarial que permite conectar fuentes de datos, construir dashboards y obtener insights para tomar decisiones.

El sistema se construye siguiendo la cadena:

**Observar → Calcular → Diagnosticar → Segmentar → Decidir → Intervenir → Medir → Aprender**

El journey prioritario es **Onboarding & Activation**, que debe resolverse a profundidad.

## 2. Rol de Claude Code como orquestador

Claude Code actúa como orquestador del proyecto:

- Planifica antes de ejecutar cada fase.
- Respeta el orden de fases definido en este documento.
- No salta pasos ni adelanta entregables de fases posteriores.
- Trata este `CLAUDE.md` como la referencia normativa por encima de cualquier atajo conveniente en el momento.

## 3. GitHub como fuente de verdad

GitHub es la fuente de verdad de los artefactos y especificaciones aprobadas. Las decisiones estratégicas aprobadas durante el trabajo deben incorporarse a la documentación correspondiente antes de ser tratadas como definitivas por el sistema.

## 4. Reglas de planificación antes de ejecución

- Ninguna fase de generación de datos, análisis, diseño de agentes o automatización se ejecuta sin un plan explícito presentado y aprobado primero.
- Prohibido generar datos, código o documentos de una sola vez sin checkpoints intermedios.
- Cada fase se cierra con commit antes de iniciar la siguiente.

## 5. El funnel de Lifecycle comienza antes del signup completo

El análisis de onboarding no puede empezar recién en la cuenta creada. El funnel debe contemplar el registro como un proceso con posible abandono, distinguiendo explícitamente:

- **`registration_started`**: la persona inició el proceso de registro.
- **`registration_completed` / `signup`**: la persona completó la creación de la cuenta.

**Registration Abandonment** (abandonar el registro entre `registration_started` y `registration_completed`) es una señal relevante de onboarding y debe poder analizarse aunque la persona nunca haya llegado a crear la cuenta.

## 6. Diferencia entre datos observados y derivados

### Datos observados / iniciales (van en el dataset crudo)

- Atributos de usuario presentes en `users.csv`.
- Eventos crudos presentes en `events.csv` (incluyendo eventos previos al signup completo, como `registration_started`).
- `converted_to_paid`, como resultado downstream observado — no se utiliza para definir Activation.

### Variables derivadas (se calculan después, nunca se generan a mano ni se embeben en el dataset inicial)

- `lifecycle_stage`
- `first_action_timestamp`
- `first_value_date`
- `days_to_first_value`
- `activation_status`
- `activation_score`
- métricas de funnel
- segmentos

**Regla explícita: si no se puede derivar de datos crudos, no es válido.**

`first_action_timestamp` se deriva de `events.csv` y representa la primera interacción significativa con el producto después del signup. El signup no cuenta como First Action.

## 7. Definiciones protegidas del caso

Estas definiciones están operacionalmente cerradas y no se reabren sin una razón explícita y documentada:

- **First Value**: conectar una fuente de datos + crear el primer dashboard + visualizar el primer insight accionable.
- **Activation**: completar First Value dentro de los primeros 7 días desde signup.
- **Late Value**: completar First Value después de los primeros 7 días.
- **Not Activated**: no haber completado First Value al momento del análisis.

Reglas de uso:

- First Value y Activation son conceptos distintos: First Value es completar la secuencia de valor; Activation es completar First Value dentro de la ventana de 7 días.
- Late Value y Not Activated no son equivalentes entre sí ni intercambiables con Activation.
- Activation no equivale a ejecutar solamente una de las tres acciones de la secuencia; requiere las tres.
- `converted_to_paid` no se utiliza para definir Activation.

## 8. Reglas de generación de datos

- `users.csv` y `events.csv` no se generan todavía; cuando se generen:
  - No deben incluir ninguna de las variables derivadas listadas en la sección 6.
  - Deben incorporar fricciones realistas (abandono de registro, usuarios que nunca alcanzan First Value, usuarios con Late Value, etc.).
  - No se fabrican patrones de datos para confirmar de antemano un bottleneck o conclusión ya decidida.
  - El signup no cuenta como First Action; los eventos de producto posteriores al signup son los que determinan First Action.

## 9. Reglas de validación

Antes de dar por válido un dataset o un cálculo derivado:

- Verificar que ninguna columna derivada prohibida (sección 6) se coló en los datos crudos.
- Verificar coherencia temporal: los eventos no pueden preceder a `registration_started`, y `registration_completed` no puede preceder a `registration_started`.
- Verificar que el diagnóstico se apoya en datos ya generados, y no que los datos se ajustaron para sostener un diagnóstico previo.

## 10. Reglas para diagnóstico

- El diagnóstico debe emerger de los datos. No se fabrican datos para demostrar un bottleneck decidido previamente.
- Todo hallazgo se documenta junto con el método de cálculo que lo produjo, de forma trazable a `users.csv` y `events.csv`.
- El diagnóstico antecede a la segmentación: no se diseñan segmentos sin diagnóstico previo.

## 11. Reglas para agentes de IA

- Cada agente debe resolver un cuello de botella identificado explícitamente en el diagnóstico, no un problema hipotético.
- Cada agente debe tener input y output explícitos y documentados.
- Ningún agente opera sobre variables derivadas que no hayan pasado por las reglas de validación (sección 9).
- Los agentes se diseñan después del diagnóstico y la segmentación, no antes.

## 12. Reglas para journeys y automatizaciones

- El journey prioritario es Onboarding & Activation.
- Las automatizaciones se diseñan después del journey y del diagnóstico correspondiente, nunca antes.
- Toda automatización debe ser trazable a una señal observada o derivada y validada (registration abandonment, not activated, late value, etc.), no a una suposición.

## 13. Definition of Done (por fase)

Una fase se considera terminada cuando:

- El plan de la fase fue presentado y aprobado antes de la ejecución.
- El resultado de la fase está commiteado en la rama de trabajo.
- La documentación generada está en español.
- No se introdujeron variables derivadas fuera del lugar que les corresponde (sección 6).
- No se contradijo ninguna definición protegida (sección 7) sin justificación explícita y documentada.

## 14. Fases del proyecto

| Fase | Entregable |
|---|---|
| 0 | `CLAUDE.md` + supuestos + esqueleto de carpetas |
| 1 | `01_CONTEXT.md` y `02_DATA_GENERATION_SPEC.md` (esquema de datos) |
| 2 | `users.csv` (10.000 usuarios) |
| 3 | `events.csv` |
| 4 | Diagnóstico cuantitativo (funnel, activación, retención, churn) |
| 5 | Segmentación |
| 6 | Customer journey por segmento (foco: Onboarding & Activation) |
| 7 | Agentes de IA |
| 8 | Automatizaciones |
| 9 | KPIs + roadmap |
| 10 | Presentación final |

Este documento (`CLAUDE.md`) corresponde a la Fase 0.

## 15. Idioma

Toda la documentación del proyecto se redacta en español.
