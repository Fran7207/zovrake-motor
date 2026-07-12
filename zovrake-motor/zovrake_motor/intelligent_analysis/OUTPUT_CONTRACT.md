# Contrato de Salida — Prompt Maestro 7

**Implementación 7.10 — Contrato oficial de integración**

## Contrato

| Propiedad | Valor |
|-----------|-------|
| Catálogo | `IntelligentAnalysisResultCatalog` v1.0 |
| Resultado por grupo | `IntelligentAnalysisGroupResult` v1.0 |
| Productor | Reasoning Result Builder (RRB) |
| Consumidores | ERP, APIs, observabilidad, auditoría |
| Entrada exclusiva | `DefinitiveComparativeModelCatalog` (PM6) |

## Principio fundamental

El **Resultado del Análisis Inteligente** es el **único punto de integración** entre el Módulo de Razonamiento Inteligente y cualquier consumidor externo.

Los consumidores **no podrán** acceder directamente a:

- Modelo Comparativo Definitivo
- Catálogos de evidencias
- Catálogos de consistencia
- Catálogos de riesgos
- Catálogos de contexto
- Catálogos de explicaciones
- Catálogos de recomendaciones

## Campos obligatorios del catálogo

| Campo | Descripción |
|-------|-------------|
| `catalog_id` | Identificador único del catálogo |
| `process_id` | Proceso de coordinación |
| `model_id` | Modelo documental de origen |
| `document_id` | Documento de origen |
| `source_evidence_catalog_id` | Referencia al catálogo de evidencias |
| `source_consistency_catalog_id` | Referencia al catálogo de consistencia |
| `source_risk_catalog_id` | Referencia al catálogo de riesgos |
| `source_context_catalog_id` | Referencia al catálogo contextual |
| `source_explanation_catalog_id` | Referencia al catálogo de explicaciones |
| `source_recommendation_catalog_id` | Referencia al catálogo de recomendaciones |
| `source_definitive_catalog_id` | Referencia al Modelo Comparativo Definitivo |
| `results` | Lista de resultados por Grupo Comparable |
| `source_data_preserved` | Debe ser `true` |

## Campos obligatorios de cada resultado (`IntelligentAnalysisGroupResult`)

| Campo | Descripción |
|-------|-------------|
| `result_id` | Identificador único del resultado |
| `group_id` | Grupo Comparable asociado |
| `definitive_model_id` | Modelo Comparativo Definitivo de origen |
| `comparative_table_id` | Cuadro comparativo asociado |
| `executive_summary` | Resumen ejecutivo del análisis |
| `structured_explanation` | Explicación estructurada (XAI) |
| `recommendation` | Recomendación fundamentada |
| `confidence_level` | Nivel de confianza coherente con evidencias |
| `document_traceability` | Trazabilidad documental consolidada |
| `source_data_preserved` | Debe ser `true` |

## Trazabilidad requerida

Cada resultado debe preservar referencias a:

- `document_id`, `definitive_model_id`, `group_id`, `comparative_table_id`
- `evidence_ids`, `risk_ids`, `explanation_segment_ids`
- `provider_ids`, `context_association_ids`
- Catálogos fuente del pipeline PM7

## Principios de Explainable AI (XAI)

1. Toda recomendación incluye justificación documentada.
2. Toda explicación referencia segmentos trazables.
3. Toda conclusión está respaldada por evidencias del modelo definitivo.
4. El nivel de confianza es coherente con la evidencia disponible.
5. Ninguna recomendación carece de respaldo documental.

## Reglas de consumo para ERP y APIs

1. Consumir exclusivamente `IntelligentAnalysisResultCatalog`.
2. Verificar `source_data_preserved == true` antes de procesar.
3. Procesar un resultado independiente por cada entrada en `results`.
4. No requerir acceso a artefactos intermedios del PM7.
5. Mantener desacoplamiento total del Frontend y del ERP.

## Evolución del contrato

Cambios al contrato requieren:

1. Nueva versión explícita del contrato.
2. Compatibilidad retroactiva o periodo de transición documentado.
3. Actualización del gobierno arquitectónico en `governance.py`.
4. Nueva certificación formal del módulo.

## Versión oficial

| Versión del módulo | Versión del contrato | Estado |
|--------------------|----------------------|--------|
| 7.10.0 | 1.0 | CERRADO — Producción |
