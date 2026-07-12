# Dynamic Row Builder — Arquitectura

**Implementación 4.4 — Prompt Maestro 6**

## Responsabilidad

Construir **filas dinámicas** para cada Cuadro Comparativo — una fila por proveedor del Grupo Comparable.

- Sin valores de celdas, organización de proveedores ni representación visual.
- Sin cantidad fija de proveedores — derivada del Modelo Comparativo de Dominio.

## Reglas de generación dinámica

1. Consumir exclusivamente catálogos del CSE y el DCB.
2. Leer `metadata_prepared.available_providers` por estructura del CSE.
3. Generar una fila por cada proveedor del grupo.
4. Asociar cada fila con las columnas del `column_set` correspondiente.
5. Reservar espacio de celdas (`cells_reserved`) sin poblar valores.
6. Cada grupo genera exclusivamente sus propias filas.

## Modelo de Fila (`ComparativeTableRowDefinition`)

| Campo | Descripción |
|-------|-------------|
| `row_id` | Identificador público único (DCR-000001) |
| `provider_id` | Identificador del proveedor |
| `logical_position` | Posición lógica en el cuadro |
| `group_id` / `table_id` | Referencia al Grupo Comparable |
| `column_references` | IDs de columnas del DCB |
| `cells_reserved` | Placeholders de celdas futuras |
| `traceability` | Cadena completa CSE → DCB → PM5 |

## Integración

- **Pipeline PM6**: etapa `construccion_filas`.
- **Coordinator**: vía `ComparativeTablesService.build_dynamic_rows()`.
- **Configuración**: `DynamicRowBuilderSettings`.

## Próximo paso

**Implementación 4.5** — Provider Organization Engine (POE).
