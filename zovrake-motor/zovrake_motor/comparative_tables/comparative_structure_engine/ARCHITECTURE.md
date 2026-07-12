# Comparative Structure Engine — Arquitectura

**Implementación 4.2 — Prompt Maestro 6**

## Responsabilidad

Construir la **estructura base** de cada Cuadro Comparativo a partir del Modelo Comparativo de Dominio (PM5).

- Una estructura independiente por cada Grupo Comparable.
- Sin columnas, filas, proveedores organizados ni representación visual.

## Modelo Base del Cuadro Comparativo

`ComparativeTableBaseStructure` contiene:

| Campo | Descripción |
|-------|-------------|
| `table_id` | Identificador público único (CTS-000001) |
| `internal_table_id` | Referencia interna inmutable |
| `group_id` / `group_type` | Grupo Comparable de origen |
| `table_status` | Estado estructural |
| `domain_reference` | Referencia al modelo PM5 |
| `columns_prepared` | Espacio reservado para DCB (4.3) |
| `rows_prepared` | Espacio reservado para DRB |
| `providers_prepared` | Espacio reservado para POE |
| `metadata_prepared` | Espacio reservado para metadatos |
| `validation_prepared` | Espacio reservado para validaciones |
| `traceability` | Cadena completa preservada desde PM5 |

## Reglas de independencia

Cada estructura es **completamente independiente**. Nunca se comparte información entre grupos.

## Integración

- **Pipeline PM6**: primera etapa funcional (`estructura_comparativa`).
- **Coordinator**: orquestación exclusiva vía `ComparativeTablesService`.
- **Configuración**: `ComparativeStructureEngineSettings` centralizada.
- **Estados/Eventos**: `ComparativeStructureMotorIntegration`.

## Próximo paso

**Implementación 4.3** — Dynamic Column Builder (DCB).
