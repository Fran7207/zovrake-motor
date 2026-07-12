# Context Evaluation Engine — Arquitectura

**Implementación 7.5 — Prompt Maestro 7 (CxEE operativo)**

## Responsabilidad

Evaluar cómo el contexto del requerimiento influye en la interpretación de evidencias sin emitir conclusiones ni recomendaciones.

## Entrada

- `EvidenceAnalysisCatalog` (EAE)
- `ConsistencyEvaluationCatalog` (CEE)
- `RiskAnalysisCatalog` (RAE)
- Modelo Comparativo Definitivo (PM6)
- Contexto del requerimiento (PM4)

vía `ContextEvaluationInputGateway`.

## Salida

`ContextEvaluationCatalog` con asociaciones contextuales, vacíos detectados y trazabilidad completa.

## Análisis contextual

1. Correspondencia requisitos comerciales ↔ evidencias comerciales
2. Correspondencia requisitos técnicos ↔ evidencias técnicas
3. Presencia/ausencia de información relevante para el contexto
4. Limitaciones derivadas del contexto
5. Alineación entre cotizaciones y objetivo del requerimiento

## Preservación

- No modifica catálogos del EAE, CEE ni RAE
- No modifica el Modelo Comparativo Definitivo
- No modifica el contexto original del requerimiento
- No accede a documentos originales

## Próximo paso

**Implementación 7.6** — Explanation Generation Engine (EGE).
