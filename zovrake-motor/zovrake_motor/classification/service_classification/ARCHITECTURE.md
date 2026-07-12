# Service Classification Engine (SCE) — Arquitectura

**Implementación 3.4 — Prompt Maestro 5**

## Responsabilidad del SCE

El **Service Classification Engine** es el único componente responsable de clasificar conceptos del CAE como **servicios**.

En esta etapa:
- Clasifica conceptos de tipo `commercial_condition`, `observation` y `technical_element` como servicios.
- **No clasifica** materiales, equivalencias ni grupos comparables.
- **No modifica** el catálogo de conceptos ni el Modelo Documental Interno.

## Flujo de clasificación

```
ServiceClassificationRequest (catálogo CAE serializado)
    → ConceptCatalogGateway.validate()     # vista de solo lectura; excluye item/partida
    → ServiceClassificationExecutor
        → CommercialConditionServiceClassifier
        → ObservationServiceClassifier
        → TechnicalElementServiceClassifier
    → ServiceCatalogBuilder               # catálogo uniforme de servicios
    → ServiceCatalogStore                 # almacén en memoria
    → Integration hooks (CNE, EDE, CGB)
```

## Modelo Interno de Servicios

Cada `ServiceRecord` conserva:

| Campo | Descripción |
|-------|-------------|
| `service_id` | Identificador interno (`sce://{model_id}/service-NNNN`) |
| `concept_id` | Referencia al concepto CAE |
| `original_name` | Nombre original del concepto |
| `description` | Descripción asociada |
| `service_scope` | Alcance del servicio cuando existe |
| `unit` / `quantity` | Unidad y cantidad cuando existen |
| `commercial_information` | Información comercial relacionada |
| `technical_information` | Especificaciones técnicas relacionadas |
| `model_reference` | Referencia al IDMB y concepto |
| `traceability` | Cadena completa hacia el documento original |

## Separación Materiales / Servicios

- El SCE **nunca** clasifica conceptos `item` ni `partida` (reservados al MCE).
- El catálogo de servicios (`ServiceCatalog`) es independiente del catálogo de materiales (`MaterialCatalog`).
- Ambos modelos evolucionan de forma autónoma.

## Integración con el CAE

- Entrada exclusiva: catálogo de conceptos del `ConceptAnalysisEngine`
- Sin acceso al documento original ni al IDMB directamente
- `source_concept_catalog_id` vincula el catálogo de servicios al catálogo CAE

## Integración con el Pipeline

Tercera etapa funcional del Pipeline de Clasificación:

```
ANALISIS_CONCEPTOS (CAE) → CLASIFICACION_MATERIALES (MCE) → CLASIFICACION_SERVICIOS (SCE) → ...
```

Ejecución oficial: `ClassificationPipeline.execute_service_classification()`

## Reglas de trazabilidad

1. Cada servicio referencia su `concept_id` del CAE.
2. `ServiceTraceability` preserva referencias canónicas, de extracción y documentales.
3. El catálogo CAE se consume en modo lectura — `concept_catalog_preserved=True`.
4. Sin acceso al documento original.

## Próximo paso

**Implementación 3.6** — Equivalence Detection Engine (EDE).
