# Concept Analysis Engine (CAE) — Arquitectura

**Implementación 3.2 — Prompt Maestro 5**

## Responsabilidad del CAE

El **Concept Analysis Engine** es el único componente responsable de identificar y estructurar conceptos candidatos presentes en el Modelo Documental Interno (IDMB).

En esta etapa:
- Identifica conceptos (ítems, partidas, elementos comerciales, técnicos, condiciones, observaciones).
- **No clasifica** materiales ni servicios.
- **No modifica** el documento original, la representación canónica ni el modelo interno.

## Flujo del análisis

```
ConceptAnalysisRequest (IDMB serializado)
    → InternalModelGateway.validate()     # vista de solo lectura
    → ConceptAnalysisExecutor
        → ItemConceptDetector
        → TechnicalConceptDetector
        → CommercialConceptDetector
        → CommercialConditionDetector
        → ObservationConceptDetector
    → ConceptCatalogBuilder               # catálogo temporal uniforme
    → TemporaryConceptCatalogStore        # almacén en memoria
    → Integration hooks (MCE, SCE, CNE)   # preparados, sin ejecución
```

## Estructura del catálogo temporal

Cada `ConceptCandidate` conserva:

| Campo | Descripción |
|-------|-------------|
| `concept_id` | Identificador temporal (`cae://{model_id}/concept-NNNN`) |
| `kind` | Tipo de concepto identificado (sin clasificación material/servicio) |
| `original_description` | Texto original del concepto |
| `location` | Sección, entidad y referencias del IDMB |
| `traceability` | Cadena completa hacia el documento original |
| `classification_pending` | `true` — preparado para MCE/SCE |

## Integración con el Pipeline

El CAE es la **primera etapa funcional** del Pipeline de Clasificación:

```
PREPARACION → ANALISIS_CONCEPTOS (CAE) → CLASIFICACION_MATERIALES → ...
```

Ejecución oficial: `ClassificationPipeline.execute_concept_analysis()`

## Integración con el Coordinator

- Entrada: `ClassificationService.analyze_concepts()`
- Estados: `PROCESANDO` → `PROCESAMIENTO_COMPLETADO`
- Eventos: módulo `classification`, categoría `processing`
- Sin comunicación directa entre componentes

## Reglas de trazabilidad

1. Cada concepto referencia `source_reference`, `canonical_reference` y `extraction_reference`.
2. `ConceptTraceability` preserva `document_reference`, `adapter_name` y `format_type`.
3. El IDMB se consume en modo lectura — `internal_model_preserved=True`.
4. Sin acceso al documento original.

## Puntos de extensión

- `ConceptDetectorRegistry.register()` — nuevos detectores
- `ConceptAnalysisEngine.extend()` — extensión del motor
- `ConceptAnalysisSettings` — configuración centralizada

## Próximo paso

**Implementación 3.3** — Material Classification Engine (MCE).
