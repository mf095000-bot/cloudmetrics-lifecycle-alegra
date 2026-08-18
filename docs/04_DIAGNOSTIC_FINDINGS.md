# Diagnostic Findings

> Fuente de verdad del diagnóstico de Lifecycle & Activation. Documento de cierre de la Fase de Diagnóstico (`CLAUDE.md`, Fase 4), calculado exclusivamente desde `users.csv` + `events.csv`. No repite metodología, p-values, coeficientes ni fórmulas — esos quedan en el historial de análisis de la fase, no aquí. Este documento existe para que Segmentación (Fase 5) pueda arrancar sin volver a interpretar los datos crudos.

---

## 1. First Value vs. Activation

- Alcanzar **First Value** (conectar fuente + crear dashboard + ver insight, alguna vez) está asociado con una tasa de conversión a pago claramente mayor que no alcanzarlo nunca (~25% vs. ~17%).
- **Llegar dentro de la ventana de 7 días (Activation) no muestra una diferencia relevante de conversión frente a llegar después de 7 días (Late Value)** — ambos grupos convierten prácticamente igual (~25%).
- **Conclusión operativa:** el foco de Lifecycle no debe reducirse a "activar en 7 días". El objetivo más defendible con evidencia es **conseguir que el usuario llegue a First Value, sin importar cuándo**. La ventana de 7 días sigue siendo relevante como métrica de velocidad (Time-to-Value), pero no debe tratarse como el corte que separa "usuario de valor" de "usuario sin valor" de cara a conversión.
- Solo ~37% de los usuarios alcanza First Value alguna vez; ~63% nunca lo alcanza (al cierre de la ventana de observación). Ahí está el margen de mejora más grande, no en acelerar a quienes ya iban a llegar.

## 2. Where users get stuck

- La fricción post-signup **está distribuida a lo largo de todo el journey**, no concentrada en un único paso.
- Entre los usuarios que nunca alcanzan First Value, el estancamiento se reparte de forma relativamente pareja entre las 5 etapas del funnel post-signup (onboarding, conexión de fuente, creación de dashboard, visualización de insight) — ninguna etapa individual concentra más de ~29% de esa población.
- **No existe un único cuello de botella que explique por sí solo la falta de Activation.** Cualquier intervención que asuma "el problema está en el onboarding" o "el problema está en conectar la fuente" estaría sobre-simplificando lo que muestran los datos.
- No se propone todavía ninguna solución — corresponde a fases posteriores.

## 3. WHO vs. WHAT

- El comportamiento de uso (número de sesiones, variedad de funcionalidades usadas, vistas de dashboard) **distingue mucho más fuertemente** entre quienes alcanzan First Value y quienes no, que cualquier atributo declarativo de cuenta (país, rol, industria, tamaño, caso de uso, canal).
- Quienes alcanzan First Value —rápido o tarde— tienen niveles de engagement casi indistinguibles entre sí, y muy por encima de quienes nunca llegan.
- **Principio para Segmentación: la segmentación no debe construirse únicamente con atributos WHO.** El comportamiento observado (WHAT) es la señal más fuerte disponible en este dataset y debe ser eje central de cualquier segmentación, no un complemento.

## 4. WHO vs. Conversion

De las 6 dimensiones de `users.csv`, estas son las que mostraron señal suficientemente consistente (persisten controlando por las demás) para justificar exploración en Segmentación:

- **`country`** — señal robusta y de la mayor magnitud entre las dimensiones WHO.
- **`role`** — señal robusta; algunos roles (notablemente Founder/CEO) convierten consistentemente menos que el resto.
- **`acquisition_channel`** — señal robusta, de magnitud moderada.
- **`company_size`** — señal secundaria: persiste, pero con una forma no lineal (empresas medianas destacan, no hay un gradiente simple chico→grande), por lo que debe tratarse con más cautela que las tres anteriores.

`industry` no mostró señal consistente sobre conversión. `use_case` mostró una señal débil y marginal, por lo que no se considera prioritaria para segmentación. `country`, `role` y `use_case` tampoco mostraron señal consistente sobre Activation una vez controlado por las demás dimensiones (solo `company_size` sobrevive ahí, como señal débil).

**Aclaración explícita: estas señales NO constituyen todavía segmentos, ni implican causalidad.** Son candidatas a explorar, no conclusiones accionables por sí mismas.

## 5. Implications for Segmentation

- La segmentación debe construirse primero sobre **comportamiento (WHAT)** — engagement, profundidad de uso, progreso en el funnel — no sobre atributos declarativos.
- Vale la pena explorar cómo `country`, `role` y `acquisition_channel` **se combinan con** el comportamiento (no como sustituto de él) para afinar segmentos, dado que son las señales WHO que sobrevivieron el control estadístico sobre conversión.
- `industry` y `use_case` **no deben convertirse automáticamente en ejes de segmentación**. Tampoco debe asumirse que cualquier atributo WHO con diferencias descriptivas constituye un segmento útil.
- La pregunta que debe responder Segmentación: **¿qué combinaciones de comportamiento (y, secundariamente, de las señales WHO robustas) definen grupos con necesidades distintas de intervención para llegar a First Value?** — no "qué segmento es mejor o peor", sino "qué segmento necesita qué".

## 6. Findings we explicitly do NOT claim

- **No afirmamos causalidad.** Ninguna asociación reportada (comportamiento, país, rol, canal, tamaño) implica que esa variable *cause* Activation o conversión — solo que se asocia con ellas en este dataset.
- **No declaramos un segmento "ganador" definitivo.** Las señales robustas (country, role, acquisition_channel) son puntos de partida para investigar, no un ranking de mejores clientes.
- **No proponemos ninguna intervención, journey ni automatización todavía.** Eso corresponde a fases posteriores del proyecto (Segmentación → Journey → Agentes → Automatización).
- **No concluimos que una sola dimensión explique Activation o conversión.** El poder explicativo conjunto de los atributos WHO sobre ambos resultados es bajo — el comportamiento (Hallazgo 3) sigue siendo la señal dominante, y ninguna dimensión individual alcanza por sí sola una magnitud que justifique tratarla como el motor único del resultado.
