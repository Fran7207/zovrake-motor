# Contrato de Salida — Prompt Maestro 6

## Identificador del contrato

| Campo | Valor |
|-------|-------|
| Nombre | `DefinitiveComparativeModelCatalog` |
| Versión | `1.0` |
| Productor | Comparative Model Builder (CMB) |
| Consumidor | Prompt Maestro 7 — Módulo de Razonamiento y Resultado del Análisis Inteligente |

## Campos obligatorios del catálogo

- `catalog_id`
- `process_id`
- `model_id`
- `document_id`
- `models`
- `pm6_definitive_output_contract`
- `pm7_input_contract_prepared`
- `source_data_preserved`

## Campos obligatorios por modelo definitivo

- `definitive_model_id`
- `comparative_table_id`
- `group_id`
- `group_type`
- `dynamic_columns`
- `dynamic_rows`
- `provider_organization`
- `commercial_information`
- `technical_information`
- `inherited_context`
- `confidence_level_available`
- `metadata`
- `traceability`
- `motor_internal_references`

## Garantías del contrato

1. **Inmutabilidad** — El catálogo no se modifica tras su certificación por CVF/CQF.
2. **Trazabilidad** — Cada modelo mantiene referencia al documento, dominio y grupo comparable.
3. **Validación** — CVF verifica integridad, consistencia y completitud.
4. **Calidad** — CQF audita cumplimiento arquitectónico antes de entrega a PM7.

## Restricciones

- No incluye recomendación de proveedor ganador
- No incluye resultado del análisis inteligente
- No aplica reglas de negocio de decisión

Estos elementos serán desarrollados en el Prompt Maestro 7.
