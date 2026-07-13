# Ciclo de Vida de Integración ERP ↔ Motor

**Implementación 9.4 — Flujo certificado E2E ERP ↔ API ↔ Motor**

## Flujo oficial

```
1. ANALYSIS_CREATED
   ERP crea el análisis (analysis_id) desde Centro de Evidencias.

2. DOCUMENTS_RECEIVED
   Documentos del Centro de Evidencias adjuntos a la solicitud.

3. VALIDATION
   API valida contrato público (campos obligatorios, documentos).

4. SENT_TO_MOTOR
   API traduce a EvidenceCenterAnalysisRequest y envía vía ECG.
   Respuesta asíncrona inmediata al ERP (APQM).

5. PROCESSING
   Coordinator → PIO → Internal API → Motor Inteligente.
   ERP puede consultar estado con query_status.

6. RESULT_GENERATED
   Motor produce IntelligentAnalysisResultCatalog.
   Disponible vía query_result.

7. RETURNED_TO_ERP
   ErpAnalysisDelivery → PublicAnalysisResponse.

8. VISUAL_UPDATE
   ERP representa el resultado en Cuadro Comparativo.
```

## Transiciones y trazabilidad

Cada transición conserva:

| Dato | Fuente |
|------|--------|
| `analysis_id` | Contrato público |
| `codigo_req` / `project_id` | Centro de Evidencias |
| Etapa (`IntegrationApiLifecycleStage`) | API |
| Eventos | `EventManager` + registro local de API |
| Estado de proceso | `StateManager` (plataforma PM8) |

## Relación con el botón Analizar Cotizaciones

En el ERP, el botón **Analizar Cotizaciones** es el disparador oficial.
En 9.4 el flujo completo quedó certificado: carga de documentos → Analizar Cotizaciones
→ API REST → Coordinator → Motor → resultado → Cuadro Comparativo.

## Manejo de fallos

| Etapa | Comportamiento |
|-------|----------------|
| Validación | `FAILED` + error controlado; no se envía al Motor |
| Procesamiento | FTRRF aísla el fallo; otros análisis continúan |
| Cancelación | Etapa `CANCELLED` (preparada) |

## Certificación E2E

Ejecutar: `python certify_integration_api_e2e.py` (12 verificaciones).
