# Contrato de Salida — Prompt Maestro 5 → Prompt Maestro 6

**Implementación 3.12 — Contrato oficial de integración**

## Contrato

| Propiedad | Valor |
|-----------|-------|
| Nombre | `ComparativeDomainModelCatalog` |
| Versión | 1.0 |
| Productor | Comparative Domain Model Builder (CDMB) |
| Consumidor | Módulo de Generación de Cuadros Comparativos (PM6) |
| Validador previo | Classification Quality Framework (CQF) |

## Principio fundamental

El **Modelo Comparativo de Dominio** es el **único punto de integración** entre Clasificación Inteligente y Generación de Cuadros Comparativos.

PM6 **no podrá** acceder directamente a:

- Documentos originales
- Representación canónica
- Modelo documental interno (IDMB)
- Catálogos intermedios (conceptos, materiales, servicios, normalización, equivalencias, grupos, asociaciones)

## Campos obligatorios del catálogo

| Campo | Descripción |
|-------|-------------|
| `catalog_id` | Identificador único del catálogo |
| `process_id` | Proceso de coordinación |
| `model_id` | Modelo documental de origen |
| `document_id` | Documento de origen |
| `source_context_association_catalog_id` | Referencia al catálogo de asociaciones |
| `models` | Lista de modelos comparativos por grupo |
| `pm6_output_contract` | Debe ser `true` |
| `source_data_preserved` | Debe ser `true` |

## Campos obligatorios de cada modelo (`ComparativeDomainModelRecord`)

| Campo | Descripción |
|-------|-------------|
| `comparative_model_id` | ID público del modelo comparativo |
| `internal_model_id` | ID interno inmutable |
| `group_id` | Grupo comparable asociado |
| `group_type` | `material` o `service` |
| `primary_item` | Ítem principal del grupo |
| `equivalent_concepts` | Conceptos equivalentes |
| `providers` | Proveedores detectados |
| `commercial_information` | Información comercial estructurada |
| `technical_information` | Información técnica estructurada |
| `related_context` | Contexto asociado preservado |
| `traceability` | Cadena completa de trazabilidad |

## Trazabilidad requerida

Cada modelo debe preservar referencias a:

- `document_id`, `model_id`, `process_id`
- `source_context_association_catalog_id`
- `source_comparable_group_catalog_id`
- `group_id`, `association_id`
- `equivalence_ids`, `concept_ids`, `normalized_concept_ids`
- `document_reference`, `canonical_reference`
- `original_preserved`, `context_preserved`

## Reglas de consumo para PM6

1. Consumir exclusivamente `ComparativeDomainModelCatalog`.
2. Verificar `pm6_output_contract == true` antes de procesar.
3. Generar un cuadro comparativo independiente por cada entrada en `models`.
4. No requerir plantillas fijas — los cuadros se construyen dinámicamente.
5. Mantener desacoplamiento total del Frontend y del ERP.

## Evolución del contrato

Cambios al contrato requieren:

1. Nueva versión explícita del contrato.
2. Compatibilidad retroactiva o periodo de transición documentado.
3. Actualización del CQF para validar la nueva versión.
4. **No modificar** los componentes congelados del PM5 sin proceso de gobierno.

## Referencia de implementación

```python
from zovrake_motor.classification.governance import closure_snapshot

snapshot = closure_snapshot()
# snapshot["output_contract"] contiene la definición canónica
```
