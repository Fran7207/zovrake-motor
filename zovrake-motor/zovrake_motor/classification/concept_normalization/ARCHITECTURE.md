# Concept Normalization Engine (CNE) — Arquitectura

**Implementación 3.5 — Prompt Maestro 5**

## Responsabilidad del CNE

El **Concept Normalization Engine** es el único componente responsable de **normalizar** la representación de conceptos clasificados.

En esta etapa:
- Normaliza materiales, servicios, partidas, especificaciones, elementos técnicos y comerciales.
- **No identifica** equivalencias ni construye grupos comparables.
- **No modifica** los valores originales ni los catálogos de origen.

## Flujo de normalización

```
ConceptNormalizationRequest (catálogos MCE + SCE serializados)
    → ClassificationCatalogGateway.validate()   # vista de solo lectura dual
    → ConceptNormalizationExecutor
        → MaterialConceptNormalizer
        → PartidaConceptNormalizer
        → ServiceConceptNormalizer
        → TechnicalElementNormalizer
        → CommercialElementNormalizer
        → SpecificationNormalizer
    → NormalizedConceptCatalogBuilder
    → NormalizedConceptCatalogStore
    → Integration hooks (EDE, CGB)
```

## Reglas de normalización

1. Cada concepto conserva simultáneamente `original_value` y `normalized_value`.
2. La normalización aplica: minúsculas, eliminación de acentos, colapso de espacios y limpieza de caracteres especiales.
3. El valor original **nunca** se reemplaza ni se sobrescribe.
4. Los catálogos MCE y SCE se consumen en modo lectura — `source_catalogs_preserved=True`.

## Modelo de Conceptos Normalizados

Cada `NormalizedConceptRecord` conserva:

| Campo | Descripción |
|-------|-------------|
| `normalized_concept_id` | Identificador interno (`cne://{model_id}/concept-NNNN`) |
| `original_value` | Valor original intacto |
| `normalized_value` | Representación normalizada |
| `concept_type` | Tipo de concepto normalizado |
| `source_category` | Origen: material, servicio o especificación |
| `concept_id` | Referencia al concepto CAE |
| `model_reference` | Referencia al registro MCE/SCE y al IDMB |
| `traceability` | Cadena completa hacia el documento original |
| `metadata` | Metadatos estructurados adicionales |

## Integración con MCE y SCE

- Entrada exclusiva: catálogos del `MaterialClassificationEngine` y `ServiceClassificationEngine`
- Sin acceso al documento original ni al catálogo CAE directamente
- `source_material_catalog_id` y `source_service_catalog_id` vinculan el catálogo normalizado

## Integración con el Pipeline

Cuarta etapa funcional del Pipeline de Clasificación:

```
CAE → MCE → SCE → NORMALIZACION_CONCEPTOS (CNE) → DETECCION_EQUIVALENCIAS → ...
```

Ejecución oficial: `ClassificationPipeline.execute_concept_normalization()`

## Reglas de trazabilidad

1. Cada concepto normalizado referencia su `concept_id` del CAE.
2. `NormalizedConceptTraceability` preserva referencias canónicas, de extracción y documentales.
3. `model_reference.source_record_id` vincula al registro MCE (`mce://`) o SCE (`sce://`).
4. Sin acceso al documento original.

## Próximo paso

**Implementación 3.6** — Equivalence Detection Engine (EDE).
