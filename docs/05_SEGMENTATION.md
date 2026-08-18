# Segmentación

> Fuente de verdad de la Fase 5 — Segmentación (`CLAUDE.md`, Fase 5). Calculado exclusivamente a partir de `users.csv` + `events.csv` y de los hallazgos ya cerrados en `docs/04_DIAGNOSTIC_FINDINGS.md`. Este documento existe para que la Fase 6 — Decidir pueda arrancar sin volver a interpretar los datos crudos ni el diagnóstico.

---

## 1. Punto de partida

La segmentación parte del diagnóstico ya cerrado (`docs/04_DIAGNOSTIC_FINDINGS.md`), en particular:

- El comportamiento/lifecycle (WHAT) es una señal más útil para segmentar que los atributos declarativos (WHO).
- La fricción post-signup está distribuida a lo largo del journey; no hay un único bottleneck dominante.
- Activation y Late Value no muestran diferencia relevante de comportamiento ni de conversión entre sí.
- `country`, `role` y `acquisition_channel` son señales WHO que sobrevivieron el control estadístico sobre conversión; `company_size` es secundaria. Ninguna se usó para definir los límites de los segmentos.

**Pregunta que responde esta fase:** ¿qué grupos de usuarios tienen necesidades de Lifecycle diferentes para llegar a First Value? — no qué segmento tiene mejores métricas.

**Eje de segmentación:** dónde se detiene cada usuario en la secuencia observable del funnel (onboarding → fuente conectada → dashboard creado → insight visualizado), y qué tan enganchado está mientras permanece ahí. Los atributos WHO no se usan para definir un segmento; solo podrían usarse después para describirlo, y en este dataset no aportaron señal diferenciadora dentro de los segmentos (sección 4).

---

## 2. Los 5 segmentos

| Segmento | Tamaño | % |
|---|---:|---:|
| 1. Sin enganche real | 1.012 | 10,1% |
| 2. Estancado en onboarding | 1.834 | 18,3% |
| 3. Configurando, sin dashboard todavía | 2.279 | 22,8% |
| 4. Dashboard creado, sin insight | 1.140 | 11,4% |
| 5. Llegó a First Value | 3.735 | 37,4% |

### 2.1 Sin enganche real (10,1%)

- **Quién es:** completó el registro (`registration_completed`) y no volvió a interactuar de forma significativa con el producto.
- **Estado observable del lifecycle:** no inició onboarding. Not Activated.
- **Dónde se detiene:** inmediatamente después del signup.
- **Comportamiento relevante:** actividad mínima (0–5 sesiones, promedio ~2), cero features usadas, cero vistas de dashboard.
- **Necesidad para avanzar hacia First Value:** un motivo para volver y empezar a usar el producto.

### 2.2 Estancado en onboarding (18,3%)

- **Quién es:** inició el onboarding pero no lo completó.
- **Estado observable del lifecycle:** último milestone alcanzado es `onboarding_started` o `profile_completed`. Not Activated.
- **Dónde se detiene:** dentro del flujo de onboarding, antes de `onboarding_completed`.
- **Comportamiento relevante:** algunas sesiones (promedio ~3,8), pero cero uso de features de producto — toda su actividad ocurre dentro del flujo de configuración, no en el producto en sí.
- **Necesidad para avanzar hacia First Value:** completar la configuración inicial.

### 2.3 Configurando, sin dashboard todavía (22,8%)

- **Quién es:** completó el onboarding y/o conectó una fuente de datos, pero nunca creó un dashboard.
- **Estado observable del lifecycle:** último milestone alcanzado es `onboarding_completed` o `data_source_connected`. Not Activated.
- **Dónde se detiene:** antes de `dashboard_created`.
- **Comportamiento relevante:** actividad moderada-alta (promedio ~6,8 sesiones), ya usa varias features distintas (~2,5 en promedio), pero cero vistas de dashboard.
- **Necesidad para avanzar hacia First Value:** dar el salto de explorar el producto a construir su primer dashboard.

### 2.4 Dashboard creado, sin insight (11,4%)

- **Quién es:** completó los dos primeros milestones de First Value (fuente conectada + dashboard creado) pero nunca llega al tercero (`insight_viewed`).
- **Estado observable del lifecycle:** último milestone alcanzado es `dashboard_created`. Not Activated.
- **Dónde se detiene:** justo antes de completar la secuencia de First Value.
- **Comportamiento relevante:** el nivel de actividad más alto entre quienes no llegan a First Value (promedio ~8,7 sesiones, ~3,0 features), y el único de estos grupos que vuelve a ver su propio dashboard de forma activa (promedio ~3,8 vistas); 24% ya comparte dashboards.
- **Necesidad para avanzar hacia First Value:** encontrar o completar el paso final hacia un insight accionable dentro de un producto que ya usa activamente.

### 2.5 Llegó a First Value (37,4%)

- **Quién es:** completó la secuencia completa (fuente conectada + dashboard creado + insight visualizado), sin importar si fue dentro o después de los 7 días desde signup.
- **Estado observable del lifecycle:** First Value alcanzado. Incluye tanto a Activated como a Late Value.
- **Dónde se detiene:** no aplica — completó la secuencia de First Value.
- **Comportamiento relevante:** el nivel de actividad más alto de todos los segmentos (promedio ~10,2 sesiones, ~3,4 features, ~4,2 vistas de dashboard), y prácticamente indistinguible entre quienes llegaron dentro de los 7 días y quienes llegaron después.
- **Necesidad para avanzar hacia First Value:** no aplica — ya lo alcanzó. Cualquier necesidad de este segmento pertenece a un journey posterior fuera del alcance de esta fase (ver sección 5).

---

## 3. Decisiones cerradas de esta fase

Las siguientes decisiones quedan cerradas y no se reabren sin una razón explícita y documentada, siguiendo la misma lógica de gobierno que `CLAUDE.md` §7 aplica a las definiciones protegidas:

1. **No se separan `Activated` y `Late Value` dentro del segmento "Llegó a First Value".** Ambos grupos muestran comportamiento y conversión a pago prácticamente idénticos; separarlos fragmentaría el segmento sin evidencia de una necesidad distinta.
2. **No se crean segmentos adicionales por `country`, `role`, `acquisition_channel`, `industry`, `use_case` ni `company_size`.** Ninguna de estas dimensiones definió el límite de un segmento.
3. **No se utiliza `converted_to_paid` para definir segmentos.** Es un resultado downstream observado, no una entrada de segmentación, consistente con la regla de `CLAUDE.md` §7 de que `converted_to_paid` no define Activation ni, por extensión, los segmentos derivados de ella.
4. **No se crea un segmento independiente basado en `dashboard_shared`.** La señal de colaboración solo aparece de forma no trivial en los Segmentos 4 y 5, en magnitudes similares entre ambos; se documenta como atributo descriptivo del Segmento 4, no como eje de un segmento propio.
5. **No se aplicó clustering ni ningún modelo.** La separación es enteramente basada en reglas de progreso observable en el funnel.
6. **No se ejecutaron nuevas rondas de pruebas estadísticas.** Esta fase reutiliza los hallazgos ya cerrados del diagnóstico (`docs/04_DIAGNOSTIC_FINDINGS.md`) y cálculos descriptivos simples sobre las variables de lifecycle ya reconstruidas.

## 4. WHO como contexto potencial (no como base de segmentación)

Las dimensiones `country`, `role`, `acquisition_channel` y `company_size` se revisaron dentro de cada uno de los 5 segmentos. En este dataset, su distribución dentro de cada segmento resultó prácticamente idéntica a la distribución global — ninguna aportó señal diferenciadora que justificara su uso ni siquiera como criterio de enriquecimiento en esta fase.

Quedan disponibles como contexto potencial para una fase posterior (p. ej. personalización de tono o canal dentro de una intervención ya decidida por comportamiento), pero no son ni fueron la base de ninguno de los 5 segmentos.

## 5. Qué no se abordó en esta fase

Esta fase define exclusivamente **quién es → qué hace → dónde está → qué necesita**, a nivel de segmento. Quedan fuera de alcance, para la fase siguiente:

- mensajes, canales, journeys, campañas, nudges, automatizaciones, agentes o prompts de agentes;
- reglas de intervención o condiciones de entrada/salida operativas;
- diseño de experimentos o medición de intervenciones.

---

## 6. Entrada a Fase 6 — Decidir

La Fase 6 deberá transformar el conocimiento fijado en este documento en una lógica de decisión operativa, siguiendo la cadena:

```text
estado del usuario → necesidad → decisión → acción → condición de salida/medición
```

Esta fase entrega los segmentos y su necesidad asociada; no desarrolla todavía esa lógica de decisión, sus reglas de entrada/salida, ni ninguna acción concreta. Ese es el trabajo de la Fase 6.
