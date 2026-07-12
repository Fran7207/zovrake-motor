# Explanation Generation Engine (EGE) — Implementación 7.6

## Responsabilidad

El **Explanation Generation Engine (EGE)** es el único componente responsable de transformar
la información producida por EAE, CEE, RAE y CxEE en explicaciones estructuradas, trazables
y fundamentadas en evidencias.

No genera conclusiones, recomendaciones, puntuaciones ni decisiones.

## Entradas (solo lectura)

| Fuente | Contrato |
|--------|----------|
| Evidence Analysis Engine | `EvidenceAnalysisCatalog` |
| Consistency Evaluation Engine | `ConsistencyEvaluationCatalog` |
| Risk Analysis Engine | `RiskAnalysisCatalog` |
| Context Evaluation Engine | `ContextEvaluationCatalog` |
| PM6 | Modelo Comparativo Definitivo (`dict`) |

Nunca accede a documentos originales.

## Salida

`ExplanationGenerationCatalog` con `ModelExplanationProfile` por Grupo Comparable.

Cada perfil contiene `ExplanationSegment` reutilizables con:

- `section_type` — resumen, evidencias, fortalezas, debilidades, riesgos, consistencia, contexto, información faltante, limitaciones
- `structured_content` — hechos estructurados (`template_key` + `facts`) para múltiples formatos e idiomas
- referencias de trazabilidad a evidencias, riesgos, inconsistencias y asociaciones contextuales

## Principios XAI

- Toda explicación se justifica con evidencias verificables
- Nunca se inventa información
- Nunca se infieren hechos no respaldados
- Preservación completa de entradas

## Integración

- **Pipeline**: fase `GENERACION_EXPLICACIONES` (orden 7)
- **Coordinator**: vía `IntelligentAnalysisService.generate_explanations()`
- **Configuración**: `ExplanationGenerationEngineSettings`
- **Estados y eventos**: `ExplanationGenerationMotorIntegration`
- **Downstream**: `ConclusionGenerationEngineIntegrationPoint` (7.7)

## Preservación

El EGE nunca modifica catálogos de entrada ni el Modelo Comparativo Definitivo.
