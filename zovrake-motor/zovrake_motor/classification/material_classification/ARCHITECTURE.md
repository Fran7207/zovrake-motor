# Material Classification Engine (MCE) — Arquitectura

**Implementación 3.3 — Prompt Maestro 5**

## Responsabilidad del MCE

El **Material Classification Engine** es el único componente responsable de clasificar conceptos del CAE como **materiales**.

En esta etapa:
- Clasifica conceptos de tipo `item` y `partida` como materiales.
- **No clasifica** servicios, equivalencias ni grupos comparables.
- **No modifica** el catálogo de conceptos ni el Modelo Documental Interno.

## Flujo de clasificación

```
MaterialClassificationRequest (catálogo CAE serializado)
    → ConceptCatalogGateway.validate()     # vista de solo lectura
    → MaterialClassificationExecutor
        → ItemMaterialClassifier
        → PartidaMaterialClassifier
    → MaterialCatalogBuilder               # catálogo uniforme de materiales
    → MaterialCatalogStore                 # almacén en memoria
    → Integration hooks (SCE, CNE, EDE, CGB)
```

## Modelo Interno de Materiales

Cada `MaterialRecord` conserva:

| Campo | Descripción |
|-------|-------------|
| `material_id` | Identificador interno (`mce://{model_id}/material-NNNN`) |
| `concept_id` | Referencia al concepto CAE |
| `original_name` | Nombre original del concepto |
| `description` | Descripción asociada |
| `unit` / `quantity` | Unidad y cantidad cuando existen |
| `commercial_information` | Precio unitario y campos comerciales |
| `technical_information` | Especificaciones técnicas relacionadas |
| `model_reference` | Referencia al IDMB y concepto |
| `traceability` | Cadena completa hacia el documento original |

## Integración con el CAE

- Entrada exclusiva: catálogo de conceptos del `ConceptAnalysisEngine`
- Sin acceso al documento original ni al IDMB directamente
- `source_concept_catalog_id` vincula el catálogo de materiales al catálogo CAE

## Integración con el Pipeline

Segunda etapa funcional del Pipeline de Clasificación:

```
ANALISIS_CONCEPTOS (CAE) → CLASIFICACION_MATERIALES (MCE) → CLASIFICACION_SERVICIOS → ...
```

Ejecución oficial: `ClassificationPipeline.execute_material_classification()`

## Reglas de trazabilidad

1. Cada material referencia su `concept_id` del CAE.
2. `MaterialTraceability` preserva referencias canónicas, de extracción y documentales.
3. El catálogo CAE se consume en modo lectura — `concept_catalog_preserved=True`.
4. Sin acceso al documento original.

## Próximo paso

**Implementación 3.4** — Service Classification Engine (SCE).
