# Equivalence Detection Engine (EDE) — Arquitectura

**Implementación 3.6 — Prompt Maestro 5**

## Responsabilidad del EDE

El **Equivalence Detection Engine** es el único componente responsable de **detectar equivalencias** entre conceptos normalizados.

En esta etapa:
- Detecta cuándo conceptos representan el mismo material o servicio.
- Identifica cuándo conceptos similares **no** son equivalentes.
- **No construye** grupos comparables ni aplica reglas de negocio.

## Criterios generales de detección

| Detector | Relación | Criterio |
|----------|----------|----------|
| ExactNormalizedMatchDetector | `equivalent` | Mismo `normalized_value` y `concept_type` |
| CrossTypeDistinctDetector | `distinct` | Mismo `normalized_value`, distinto `concept_type` |
| SharedOriginRelationDetector | `related` | Mismo `concept_id` CAE, representaciones distintas |

## Flujo de detección

```
EquivalenceDetectionRequest (catálogo CNE serializado)
    → NormalizedConceptCatalogGateway.validate()
    → EquivalenceDetectionExecutor
        → ExactNormalizedMatchDetector
        → CrossTypeDistinctDetector
        → SharedOriginRelationDetector
    → EquivalenceCatalogBuilder
    → EquivalenceCatalogStore
    → Integration hooks (CGB, Context, Domain Model)
```

## Modelo de Equivalencias

Cada `EquivalenceRecord` conserva:

| Campo | Descripción |
|-------|-------------|
| `equivalence_id` | Identificador interno (`ede://{model_id}/equivalence-NNNN`) |
| `involved_concept_ids` | Conceptos normalizados involucrados |
| `relation_type` | `equivalent`, `distinct` o `related` |
| `evidence_level` | `high`, `medium` o `low` |
| `status` | Estado de la detección |
| `explainability` | Criterios, información usada y limitaciones |
| `traceability` | Cadena hacia el catálogo normalizado y documento |

## Principios de explicabilidad

Cada relación incluye `EquivalenceExplainability` con:
- `criteria_used` — reglas aplicadas
- `information_used` — datos estructurados evaluados
- `limitations` — restricciones de esta etapa
- `rationale` — justificación textual para módulos posteriores

## Integración con el Pipeline

Quinta etapa funcional:

```
CNE → DETECCION_EQUIVALENCIAS (EDE) → CONSTRUCCION_GRUPOS → ...
```

Ejecución oficial: `ClassificationPipeline.execute_equivalence_detection()`

## Próximo paso

**Implementación 3.7** — Comparable Group Builder (CGB).
