# Group Integrity Engine — Arquitectura

**Implementación 4.6 — Prompt Maestro 6**

## Responsabilidad

Verificar **integridad estructural** de cada Cuadro Comparativo de forma no destructiva.

- Sin modificar, corregir ni reorganizar datos.
- Sin comparar, recomendar ni aplicar reglas de negocio.

## Reglas de validación

1. Consumir exclusivamente catálogos del CSE, DCB, DRB y POE.
2. Validar grupos, columnas, filas y proveedores por Grupo Comparable.
3. Detectar duplicados, referencias rotas e inconsistencias.
4. Registrar hallazgos sin alterar información original.
5. Preparar reporte para Traceability & Metadata Engine.

## Criterios de integridad

| Área | Verificaciones |
|------|----------------|
| Grupo | ID válido, relación con dominio, referencias |
| Columnas | IDs únicos, pertenencia al grupo |
| Filas | IDs únicos, pertenencia al grupo, refs a columnas |
| Proveedores | Sin duplicados, refs a filas/columnas/documentos |
| General | Consistencia entre catálogos |

## Integración

- **Pipeline PM6**: etapa `integridad_grupos`.
- **Coordinator**: vía `ComparativeTablesService.validate_group_integrity()`.
- **Configuración**: `GroupIntegrityEngineSettings`.

## Próximo paso

**Implementación 4.7** — Traceability & Metadata Engine (TME).
