# Risk Analysis Engine — Arquitectura

**Implementación 7.4 — Prompt Maestro 7 (RAE operativo)**

## Responsabilidad

Identificar, clasificar y registrar riesgos a partir de evidencias (EAE) y consistencia (CEE) sin interpretar, concluir ni recomendar.

## Entrada

- `EvidenceAnalysisCatalog` (EAE)
- `ConsistencyEvaluationCatalog` (CEE)

vía `EvidenceAndConsistencyInputGateway`.

## Salida

`RiskAnalysisCatalog` con perfiles de riesgo por modelo, riesgos categorizados y trazabilidad completa.

## Categorías de riesgo

1. Riesgo documental
2. Riesgo comercial
3. Riesgo técnico
4. Riesgo de información
5. Riesgo de consistencia

## Preservación

- No modifica el catálogo de evidencias del EAE
- No modifica el catálogo de consistencia del CEE
- No accede al Modelo Comparativo Definitivo ni documentos originales
- Registra riesgos sin resolverlos automáticamente

## Próximo paso

**Implementación 7.5** — Context Evaluation Engine (CxEE).
