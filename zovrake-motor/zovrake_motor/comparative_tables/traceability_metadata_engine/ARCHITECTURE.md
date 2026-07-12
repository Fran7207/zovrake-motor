# Traceability & Metadata Engine (TME) — Implementación 4.7

## Responsabilidad

El **Traceability & Metadata Engine (TME)** es el único componente responsable de enriquecer cada Cuadro Comparativo con trazabilidad documental, contexto heredado, nivel de confianza y metadatos de auditoría.

**No modifica** documentos originales, estructura, columnas, filas, proveedores ni resultados de validación.

## Reglas de preservación

| Regla | Descripción |
|-------|-------------|
| Inmutabilidad de origen | Los catálogos CSE, DCB, DRB, POE y el reporte GIE permanecen intactos |
| Contexto heredado | `inherited_context` se copia sin alteración desde CSE |
| Nivel de confianza | `confidence_level_available` se conserva sin recalcular |
| Trazabilidad documental | Referencias a documento, modelo interno y dominio preservadas |
| Sin decisiones | No aplica reglas de negocio ni recomendaciones |

## Estructura de trazabilidad

Cada `EnrichedComparativeTable` incluye:

- `document_evidence` — documento original, representación documental, modelo interno
- `comparable_group` — Grupo Comparable y Modelo Comparativo de Dominio
- `context_association_id` — contexto asociado
- `provider_references` — trazabilidad por proveedor
- `lineage` — cadena heredada desde PM5
- Referencias a catálogos upstream y reporte GIE

## Estructura de metadatos

- `internal_identifiers` — IDs internos del Motor
- `group_type`, `model_version`, `processing_timestamp`
- `processing_status`, `integrity_status`
- `audit_info` — enriquecedor, timestamp de registro
- `motor_internal_references` — IDs de catálogos fuente
- `inherited_metadata` — metadatos heredados sin modificación

## Integración

| Componente | Relación |
|------------|----------|
| CSE, DCB, DRB, POE, GIE | Consumo exclusivo de catálogos y reporte (solo lectura) |
| Pipeline PM6 | Etapa 8 — `TRAZABILIDAD_METADATOS` |
| Coordinator | Coordinación exclusiva vía Pipeline/Service |
| Configuración | `TraceabilityMetadataEngineSettings` |
| Estados / Eventos | `TraceabilityMetadataMotorIntegration` |
| CMB (4.8) | `ComparativeModelBuilderIntegrationPoint` preparado |

## Próximo paso

**Implementación 4.8** — Comparative Model Builder (CMB): construcción del Modelo Comparativo definitivo.
