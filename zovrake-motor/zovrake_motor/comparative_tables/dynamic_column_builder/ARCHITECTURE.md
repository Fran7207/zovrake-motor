# Dynamic Column Builder — Arquitectura

**Implementación 4.3 — Prompt Maestro 6**

## Responsabilidad

Construir **columnas dinámicas** para cada Cuadro Comparativo a partir de la estructura base del CSE.

- Sin filas, proveedores organizados ni valores de proveedor.
- Sin plantillas fijas — columnas derivadas de atributos realmente presentes.

## Reglas de generación dinámica

1. Consumir exclusivamente el catálogo de estructuras del CSE.
2. Leer `metadata_prepared.available_attributes` por estructura.
3. Generar una columna por cada atributo comercial, técnico y especificación.
4. Incluir `primary_item` si está disponible.
5. Eliminar duplicados por nombre normalizado dentro del mismo grupo.
6. Cada grupo genera exclusivamente sus propias columnas.

## Modelo de Columna (`ComparativeTableColumnDefinition`)

| Campo | Descripción |
|-------|-------------|
| `column_id` | Identificador público único (DCC-000001) |
| `attribute_name` | Nombre del atributo |
| `data_type` | Tipo inferido dinámicamente |
| `logical_position` | Posición lógica en el cuadro |
| `group_id` / `table_id` | Referencia al Grupo Comparable |
| `traceability` | Cadena completa desde CSE/PM5 |

## Integración

- **Pipeline PM6**: etapa `construccion_columnas`.
- **Coordinator**: vía `ComparativeTablesService.build_dynamic_columns()`.
- **Configuración**: `DynamicColumnBuilderSettings`.

## Próximo paso

**Implementación 4.4** — Dynamic Row Builder (DRB) — operativo.
**Implementación 4.5** — Provider Organization Engine (POE).
