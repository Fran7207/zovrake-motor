# Contrato Público de Integración — Prompt Maestro 9

**Implementación 9.2 — Contrato estable ERP ↔ API REST ↔ Motor**

## Contrato

| Propiedad | Valor |
|-----------|-------|
| Nombre | `PublicIntegrationApi` |
| Versión | **v1** |
| Productor ERP | Centro de Evidencias — Cotizaciones |
| Disparador | Botón **Analizar Cotizaciones** |
| Consumidor Motor | vía `ErpCommunicationGateway` (PM8) |
| Salida estructurada | referencia a `IntelligentAnalysisResultCatalog` v1.0 |

## Campos mínimos del contrato

| Campo | Descripción |
|-------|-------------|
| `analysis_id` | Identificador único del análisis (`UUID`) |
| `codigo_req` | Identificador del requerimiento |
| `project_id` | Identificador del proyecto / obra |
| `quotation_id` | Identificador de cotización (opcional) |
| `documents` | Documentos enviados desde Centro de Evidencias |
| `requirement` | Contexto del requerimiento |
| `metadata` | Metadatos extensibles |
| `status` | Estado actual del ciclo de vida |
| `result` | Resultado estructurado |
| `error` | Error controlado |

## Transporte HTTP (9.2)

| Operación REST | Operación de servicio | Modelo de entrada | Modelo de salida |
|----------------|----------------------|-------------------|------------------|
| `POST /api/v1/analyses` | `start_analysis` | `CreateAnalysisPayload` → `PublicAnalysisRequest` | `ApiResponseEnvelope` |
| `GET /api/v1/analyses/{id}/status` | `query_status` | `PublicStatusQuery` | `ApiResponseEnvelope` |
| `GET /api/v1/analyses/{id}/result` | `query_result` | `PublicResultQuery` | `ApiResponseEnvelope` |

Todas las respuestas HTTP usan `ApiResponseEnvelope` con los campos del contrato público.

## Operaciones oficiales (servicio)

| Operación | Modelo de entrada | Modelo de salida |
|-----------|-------------------|------------------|
| `start_analysis` | `PublicAnalysisRequest` | `PublicAnalysisResponse` |
| `query_status` | `PublicStatusQuery` | `PublicAnalysisResponse` |
| `query_result` | `PublicResultQuery` | `PublicAnalysisResponse` |

## Mapeo hacia PM8 (sin romper compatibilidad)

| API Pública | ECG / Internal API (PM8) |
|-------------|--------------------------|
| `analysis_id` | `process_id` |
| `PublicAnalysisRequest` | `EvidenceCenterAnalysisRequest` |
| `PublicStatusQuery` | `EvidenceCenterStatusQuery` |
| `PublicResultQuery` | `EvidenceCenterResultQuery` |
| `PublicAnalysisResponse` | `ErpAnalysisDelivery` |

## Errores controlados

| Código | Significado |
|--------|-------------|
| `invalid_document` | Documento inválido |
| `unreadable_file` | Archivo ilegible |
| `unsupported_format` | Formato no soportado |
| `incomplete_request` | Solicitud incompleta |
| `internal_error` | Error interno |
| `processing_cancelled` | Procesamiento cancelado |
| `validation_failed` | Validación fallida |
| `not_found` | Análisis no encontrado |
| `contract_violation` | Violación de contrato |

Un error en un análisis **no** detiene otros análisis ni el resto del sistema.

## Evolución sin ruptura

1. `contract_version` viaja en toda solicitud/respuesta.
2. Nuevas versiones (`v2+`) coexistirán con `v1`.
3. Campos nuevos se agregarán de forma aditiva en `metadata` o versiones futuras.
4. El contrato PM8 (`InternalIntegrationApi` v1) permanece **congelado**.

## Autenticación / autorización

Preparadas arquitectónicamente (`authentication_prepared`, `authorization_prepared`).
**No implementadas** en 9.2 ni como requisito de esta implementación.
