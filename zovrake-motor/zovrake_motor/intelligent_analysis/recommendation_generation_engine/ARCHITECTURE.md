# Recommendation Generation Engine (RGE) — Implementación 7.7

## Responsabilidad

El **Recommendation Generation Engine (RGE)** genera recomendaciones fundamentadas como
apoyo a la decisión. Nunca sustituye el criterio humano.

## Entradas (solo lectura)

| Fuente | Contrato |
|--------|----------|
| EAE | `EvidenceAnalysisCatalog` |
| CEE | `ConsistencyEvaluationCatalog` |
| RAE | `RiskAnalysisCatalog` |
| CxEE | `ContextEvaluationCatalog` |
| EGE | `ExplanationGenerationCatalog` |
| PM6 | Modelo Comparativo Definitivo |

## Escenarios soportados

| Escenario | Condición | Salida |
|-----------|-----------|--------|
| **A — CLEAR_WINNER** | Proveedor con respaldo claramente superior | `recommended_provider_id`, justificación, fortalezas, riesgos |
| **B — EQUIVALENT_ALTERNATIVES** | Proveedores con puntuación equivalente | Alternativas documentadas sin ganador |
| **C — INSUFFICIENT_INFORMATION** | Evidencias insuficientes | Sin proveedor recomendado, acciones sugeridas |

## Nivel de confianza

Derivado de: cobertura de evidencias, consistencia, riesgos, vacíos contextuales.
Niveles: `high`, `medium`, `low`.

## Integración

- **Pipeline**: fase `GENERACION_RECOMENDACIONES`
- **Downstream**: `ReasoningResultBuilderIntegrationPoint` (7.8)

## Preservación

El RGE nunca modifica catálogos de entrada ni el Modelo Comparativo Definitivo.
