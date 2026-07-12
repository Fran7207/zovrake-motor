# Classification Quality Framework (CQF) — Arquitectura

**Implementación 3.10 — Prompt Maestro 5**

## Responsabilidad del CQF

El **Classification Quality Framework** es el único componente responsable de **validar la calidad** de toda la clasificación inteligente.

En esta etapa:
- Valida consistencia, integridad, unicidad y trazabilidad.
- Genera un **informe interno** preparado para certificación (3.11).
- **No modifica** ningún dato evaluado.
- **No certifica** oficialmente el módulo (certificación en 3.11 — completada).

## Validadores (5)

| Validador | Categoría | Verifica |
|-----------|-----------|----------|
| ModelConsistencyValidator | Consistencia | Coherencia del modelo comparativo, tipos, contexto |
| DataIntegrityValidator | Integridad | Campos obligatorios, referencias, preservación |
| IdentifierUniquenessValidator | Unicidad | IDs duplicados de modelos y grupos |
| TraceabilityChainValidator | Trazabilidad | Cadena documento → modelo comparativo |
| PipelineFlowValidator | Pipeline | Componentes PM5 listos en el flujo |

## Informe de validación

`ClassificationQualityReport` incluye:
- `checks_executed`, `checks_passed`, `checks_failed`
- `findings` con severidad (info, warning, error)
- `overall_status`: `passed`, `passed_with_warnings`, `failed`, `skipped`
- `certification_prepared=True`

## Integración con el Pipeline

Etapa de validación del PM5 (después de MODELO_DOMINIO):

```
CDMB → VALIDACION_CALIDAD (CQF) → FINALIZACION
```

Ejecución oficial: `ClassificationPipeline.execute_quality_validation()`

## Estado post-certificación

La certificación oficial del módulo se completó en la **Implementación 3.11**. El CQF permanece como guardián de calidad antes de entregar el Modelo Comparativo al **Prompt Maestro 6**.
