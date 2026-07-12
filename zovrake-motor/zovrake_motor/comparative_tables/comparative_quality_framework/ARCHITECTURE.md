# Comparative Quality Framework (CQF) — Implementación 4.10

## Responsabilidad

Auditar de forma **no destructiva** la calidad arquitectónica, funcional y estructural del Módulo de Generación de Cuadros Comparativos (PM6) antes de su certificación.

El CQF es el **único** componente autorizado para esta auditoría integral.

## Alcance de la auditoría

| Categoría | Auditor |
|-----------|---------|
| Arquitectónica | `architectural_compliance_validator` |
| Consistencia de modelos | `definitive_model_consistency_validator` |
| Integridad del reporte CVF | `validation_report_integrity_validator` |
| Unicidad de identificadores | `identifier_uniqueness_validator` |
| Trazabilidad documental | `traceability_chain_validator` |
| Continuidad del Pipeline | `pipeline_flow_validator` |

## Criterios de aceptación

Definidos en `governance.py` — `CQF_ACCEPTANCE_CRITERIA`.

## Contrato de entrada

Consume exclusivamente:

- Catálogo definitivo del **Comparative Model Builder** (CMB)
- Reporte de validación del **Comparative Validation Framework** (CVF)
- Snapshot opcional del Pipeline PM6

**No** accede a documentos originales.

## Integración

| Sistema | Rol |
|---------|-----|
| Pipeline PM6 | Etapa 11 — `VALIDACION_CALIDAD` |
| Coordinator | Orquestación vía `ComparativeTablesPipeline` |
| Configuración | `ComparativeQualityFrameworkSettings` |
| Estados | `StateManager` vía `ComparativeQualityMotorIntegration` |
| Eventos | `EventManager` vía `ComparativeQualityMotorIntegration` |
| Certificación (4.11) | `ModuleCertificationIntegrationPoint` preparado |

## Preservación de información

- No modifica catálogo definitivo
- No modifica reporte de validación
- No corrige inconsistencias
- Conserva trazabilidad completa

## Próximo paso

**Implementación 4.11** — Integración y Certificación Completa del Módulo PM6.
