# Comparative Domain Model Builder (CDMB) — Arquitectura

**Implementación 3.9 — Prompt Maestro 5**

## Responsabilidad del CDMB

El **Comparative Domain Model Builder** es el único componente responsable de construir el **Modelo Comparativo de Dominio**.

Este modelo es la **salida oficial del Prompt Maestro 5** y la **entrada oficial del Prompt Maestro 6**.

En esta etapa:
- Agrega grupos comparables, contexto, materiales, servicios y trazabilidad.
- Asigna identificadores únicos (`CDM-000001`, …).
- **No genera** cuadros comparativos ni recomendaciones.

## Estructura del Modelo Comparativo

Cada `ComparativeDomainModelRecord` incluye:

| Campo | Descripción |
|-------|-------------|
| `comparative_model_id` | Identificador público (`CDM-000001`) |
| `group_id` | Grupo Comparable origen |
| `group_type` | `material` o `service` |
| `primary_item` | Material o servicio principal |
| `equivalent_concepts` | Conceptos normalizados equivalentes |
| `providers` | Proveedores asociados |
| `commercial_information` | Información comercial |
| `technical_information` | Información técnica |
| `related_context` | Contexto preservado del requerimiento |
| `confidence_level_available` | Nivel de confianza (`not_evaluated`) |
| `traceability` | Cadena completa hacia origen |

## Contrato de salida (PM5 → PM6)

`ComparativeDomainModelCatalog` con `pm6_output_contract=True`:

- Todo Cuadro Comparativo futuro se generará exclusivamente desde este modelo.
- Nunca desde documentos originales.
- Sin transformaciones adicionales requeridas por el PM6.

## Flujo de construcción

```
ComparativeDomainModelBuildRequest (catálogo CAE-Context)
    → ContextAssociationCatalogGateway.validate()
    → ComparativeDomainModelBuildExecutor
        → GroupContextAggregationBuilder
    → ComparativeDomainModelCatalogStore
```

## Integración con el Pipeline

Última etapa funcional del PM5:

```
CAE-Context → MODELO_DOMINIO (CDMB) → FINALIZACION
```

Ejecución oficial: `ClassificationPipeline.execute_comparative_domain_model_build()`

## Próximo paso

**Implementación 3.10** — Classification Quality Framework (CQF).
