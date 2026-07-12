# Comparative Validation Framework — Implementación 4.9

## Responsabilidad

El **Comparative Validation Framework (CVF)** valida que cada Modelo Comparativo Definitivo sea consistente, íntegro, completo y estable antes de su certificación.

**No modifica** datos ni corrige inconsistencias automáticamente.

## Reglas de validación

| Categoría | Verificaciones |
|-----------|----------------|
| Estructural | Identificadores, grupo, cuadro comparativo |
| Completitud | Campos obligatorios del contrato PM6 |
| Integridad | Referencias rotas, columnas/filas/proveedores huérfanos |
| Consistencia | Duplicados de IDs a nivel modelo y catálogo |
| Trazabilidad | Documento, grupo, referencias internas del Motor |

## Criterios de aceptación

- `structural_completeness`
- `referential_integrity`
- `identifier_consistency`
- `traceability_preservation`
- `contract_compliance`

## Integración

| Componente | Relación |
|------------|----------|
| CMB | Consumo exclusivo del catálogo definitivo |
| Pipeline PM6 | Etapa 10 — `VALIDACION_COMPARATIVA` |
| CQF (4.10) | `ComparativeQualityFrameworkIntegrationPoint` preparado |

## Próximo paso

**Implementación 4.10** — Comparative Quality Framework (CQF).
