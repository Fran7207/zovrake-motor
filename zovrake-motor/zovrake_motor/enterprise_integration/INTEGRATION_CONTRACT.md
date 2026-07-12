# Contrato Oficial de Integracion — Prompt Maestro 8

**Implementacion 8.12 — Contrato oficial ERP ↔ Motor Inteligente**

## Contrato

| Propiedad | Valor |
|-----------|-------|
| API | `InternalIntegrationApi` v1 |
| Canal ERP | `ErpCommunicationGateway` |
| Coordinador | `EnterpriseIntegrationCoordinator` |
| Punto de entrada ERP | Centro de Evidencias — Cotizaciones |
| Salida oficial | `IntelligentAnalysisResultCatalog` v1.0 (PM7) |

## Principio fundamental

La **Internal Integration API v1** es el **unico contrato oficial** de comunicacion entre el ERP ZOVRAKE y el Motor Inteligente.

Toda interaccion debera realizarse mediante:

1. **ERP Communication Gateway (ECG)**
2. **Internal Integration API**
3. **Integration Coordinator**

## Operaciones oficiales (v1)

| Operacion | Descripcion |
|-----------|-------------|
| `start_analysis` | Inicia analisis desde Centro de Evidencias |
| `query_status` | Consulta estado del proceso |
| `query_result` | Obtiene Resultado del Analisis Inteligente |
| `cancel_analysis` | Cancela proceso (preparado) |
| `validate_request` | Valida solicitud conforme al contrato |

## Campos obligatorios — start_analysis

| Campo | Descripcion |
|-------|-------------|
| `process_id` | Identificador unico del proceso |
| `codigo_req` | Codigo del requerimiento |
| `contract_version` | Version del contrato (`v1`) |

## Respuestas oficiales

| Tipo | Campos obligatorios |
|------|---------------------|
| `start_analysis_response` | process_id, success, message, occurred_at, processing_status |
| `analysis_status_response` | process_id, success, message, occurred_at, processing_status |
| `analysis_result_response` | process_id, success, message, occurred_at, processing_status |
| `internal_api_error_response` | error_code, message, occurred_at |

## Accesos prohibidos

Desde el modulo `enterprise_integration`, queda **prohibido** importar directamente:

- `zovrake_motor.intelligent_analysis`
- `zovrake_motor.comprehension`
- `zovrake_motor.classification`
- `zovrake_motor.comparative_tables`
- `zovrake_motor.reception`
- `zovrake_motor.documents`

## Reglas de extension futura

1. Nuevas versiones de contrato (`v2+`) deberan coexistir sin ruptura con `v1`.
2. Nuevos canales de transporte (HTTP, colas) deberan respetar ECG como frontera ERP.
3. Nuevos modulos del Motor deberan integrarse via Internal Integration API.
4. El contrato de salida `IntelligentAnalysisResultCatalog` permanece inmutable (PM7 CERRADO).

## Estado

| Atributo | Valor |
|----------|-------|
| Prompt Maestro 8 | CERRADO |
| Version del contrato | v1 (congelada) |
| Implementacion de cierre | 8.12 |
