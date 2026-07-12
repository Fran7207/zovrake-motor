# Comparable Group Builder (CGB) — Arquitectura

**Implementación 3.7 — Prompt Maestro 5**

## Responsabilidad del CGB

El **Comparable Group Builder** es el único componente responsable de **construir Grupos Comparables** a partir del Modelo de Equivalencias.

En esta etapa:
- Agrupa únicamente conceptos con relación `equivalent`.
- Asigna identificadores únicos, estables e inmutables (`GC-000001`, `GC-000002`, …).
- **No genera** cuadros comparativos, recomendaciones ni puntuaciones.
- **No accede** a documentos originales ni modifica el Modelo Documental Interno.

## Reglas de construcción de grupos

| Regla | Descripción |
|-------|-------------|
| Entrada exclusiva | Catálogo de equivalencias del EDE |
| Relaciones válidas | Solo `relation_type == equivalent` |
| Algoritmo | Union-Find sobre pares equivalentes |
| Tipo de grupo | `material` o `service` (inferido de `shared_concept_type`) |
| Mínimo de miembros | Configurable (`min_members_per_group`, default: 1) |
| Inmutabilidad | El catálogo de equivalencias no se modifica |

## Ciclo de vida del identificador único

| Identificador | Formato | Propiedad |
|---------------|---------|-----------|
| `group_id` | `GC-000001` (prefijo + 6 dígitos) | Público, estable, inmutable |
| `internal_group_id` | `cgb://{model_id}/group-NNNN` | Referencia interna del motor |

La secuencia numérica se asigna en orden determinista (orden lexicográfico del primer miembro del clúster).

## Modelo de Grupo Comparable

Cada `ComparableGroupRecord` incluye:

| Campo | Descripción |
|-------|-------------|
| `group_id` | Identificador público inmutable |
| `internal_group_id` | Identificador interno del motor |
| `group_type` | `material` o `service` |
| `normalized_concept_ids` | Conceptos normalizados del grupo |
| `concept_ids` | Conceptos CAE asociados |
| `equivalence_ids` | Relaciones de equivalencia que forman el grupo |
| `provider_references` | Referencias a proveedores |
| `commercial_information` | Información comercial estructurada |
| `technical_information` | Especificaciones e información técnica |
| `model_reference` | Referencias al Modelo Documental Interno |
| `traceability` | Cadena completa hacia documento, equivalencias y conceptos |

## Flujo de construcción

```
ComparableGroupBuildRequest (catálogo EDE serializado)
    → EquivalenceCatalogGateway.validate()
    → ComparableGroupBuildExecutor
        → EquivalenceClusterGroupBuilder (Union-Find)
    → ComparableGroupCatalogBuilder
    → ComparableGroupCatalogStore
    → Integration hooks (Context Association, Domain Model)
```

## Integración con el Pipeline

Séptima etapa funcional:

```
EDE → CONSTRUCCION_GRUPOS (CGB) → IDENTIFICACION_GRUPOS → ASOCIACION_CONTEXTO → ...
```

Ejecución oficial: `ClassificationPipeline.execute_comparable_group_build()`

## Trazabilidad

Cada grupo conserva:
- Documento original (referencia, no acceso directo)
- Representación canónica
- Modelo documental interno
- Concepto identificado y normalizado
- Relación de equivalencia origen

## Próximo paso

**Implementación 3.8** — Context Association Engine (CAE-Context).
