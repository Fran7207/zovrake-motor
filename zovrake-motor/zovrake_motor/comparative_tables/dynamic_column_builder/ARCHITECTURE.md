Dynamic Column Builder — Arquitectura
Implementación 4.3 — Prompt Maestro 6
Responsabilidad
Construir columnas dinámicas para cada Cuadro Comparativo a partir de la estructura base del CSE.
Sin filas, proveedores organizados ni valores de proveedor.
Sin plantillas fijas — columnas derivadas de atributos realmente presentes.
Reglas de generación dinámica
Consumir exclusivamente el catálogo de estructuras del CSE.
Leer `metadata_prepared.available_attributes` por estructura.
Generar una columna por cada atributo comercial, técnico y especificación.
Incluir `primary_item` si está disponible.
Eliminar duplicados por nombre normalizado dentro del mismo grupo.
Cada grupo genera exclusivamente sus propias columnas.
Modelo de Columna (`ComparativeTableColumnDefinition`)
Campo	Descripción
`column_id`	Identificador público único (DCC-000001)
`attribute_name`	Nombre del atributo
`data_type`	Tipo inferido dinámicamente
`logical_position`	Posición lógica en el cuadro
`group_id` / `table_id`	Referencia al Grupo Comparable
`traceability`	Cadena completa desde CSE/PM5
Integración
Pipeline PM6: etapa `construccion_columnas`.
Coordinator: vía `ComparativeTablesService.build_dynamic_columns()`.
Configuración: `DynamicColumnBuilderSettings`.
Próximo paso
Implementación 4.4 — Dynamic Row Builder (DRB) — operativo.
Implementación 4.5 — Provider Organization Engine (POE).
Implementación 4.12 — Alineamiento semántico de atributos (ZO-047)
El constructor no trata etiquetas equivalentes como columnas diferentes.
Se introduce una identidad semántica conservadora para aliases comerciales frecuentes:
`CANT.`, `CANTIDAD`, `QTY` → `QUANTITY` / `Cantidad`
`UNID.`, `UM`, `U.MEDIDA`, `UNIDAD` → `UNIT` / `Unidad`
`S/P.U.`, `P.U.`, `PU`, `PRECIO UNITARIO` → `UNIT_PRICE` / `Precio Unitario`
`S/.TOTAL`, `PRECIO TOTAL`, `IMPORTE`, `TOTAL` en alcance de ítem → `LINE_TOTAL` / `Total`
`TOTAL A PAGAR`, `TOTAL GENERAL` → `DOCUMENT_TOTAL` / `Total del Documento`
La etiqueta original se conserva en metadata y los atributos no reconocidos siguen siendo
atributos libres. El alcance (`item`/`document`) evita confundir el total de una línea con
el total global del documento.
El llenado de PM6 utiliza la identidad semántica de la columna, por lo que una columna
creada a partir de `S/P.U.` puede recuperar correctamente `unit_price` y una columna
creada a partir de `S/.TOTAL` puede recuperar `total` del ítem fuente.