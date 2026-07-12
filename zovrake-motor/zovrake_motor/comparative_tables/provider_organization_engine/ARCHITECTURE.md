# Provider Organization Engine — Arquitectura

**Implementación 4.5 — Prompt Maestro 6**

## Responsabilidad

Organizar **proveedores** dentro de cada Cuadro Comparativo de forma determinística y trazable.

- Sin comparar, recomendar, puntuar ni aplicar reglas de negocio.
- Sin modificar información original de proveedores.

## Reglas de organización

1. Consumir exclusivamente catálogos del CSE, DCB y DRB.
2. Una organización por proveedor-fila del grupo.
3. Orden determinístico por `provider_id`.
4. Detectar duplicados e informar incidencias — sin corrección automática.
5. Cada grupo organiza exclusivamente sus propios proveedores.

## Modelo del Proveedor (`OrganizedProviderRecord`)

| Campo | Descripción |
|-------|-------------|
| `organization_id` | Identificador público único (DOP-000001) |
| `provider_id` | Identificador del proveedor |
| `row_id` / `row_reference` | Referencia a la fila del DRB |
| `document_reference` | Referencia documental heredada |
| `commercial_information` | Información comercial heredada |
| `technical_information` | Información técnica heredada |
| `inherited_context` | Contexto heredado del grupo |
| `confidence_level_available` | Nivel de confianza heredado |
| `traceability` | Cadena completa CSE → DCB → DRB → PM5 |

## Integración

- **Pipeline PM6**: etapa `organizacion_proveedores`.
- **Coordinator**: vía `ComparativeTablesService.organize_providers()`.
- **Configuración**: `ProviderOrganizationEngineSettings`.

## Próximo paso

**Implementación 4.6** — Group Integrity Engine (GIE).
