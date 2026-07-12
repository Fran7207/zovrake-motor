# Asynchronous Processing & Queue Manager — Arquitectura (Implementación 8.5)

## Responsabilidad

El **Asynchronous Processing & Queue Manager (APQM)** es el **único componente** autorizado para administrar el procesamiento asíncrono de solicitudes de análisis provenientes del ERP.

Garantiza que el ERP **nunca espere** a que el Motor Inteligente complete el análisis.

## Arquitectura de procesamiento asíncrono

```
Centro de Evidencias (ERP)
        │
        ▼
ErpCommunicationGateway.submit_analysis_request
        │
        ├─ respuesta inmediata ErpAnalysisDelivery (procesamiento_pendiente)
        │
        ▼
AsyncProcessingQueueManager.enqueue_start_analysis
        │
        ▼
Cola lógica (ApqmQueueStore) — FIFO en memoria
        │
        ▼
AsyncQueueWorker
        │
        ▼
EnterpriseIntegrationApqmExecutor
        │
        ▼
Coordinator → PIO → Internal API → Motor (preparado)
```

## Gestión de colas

| Concepto | Implementación |
|----------|----------------|
| Cola lógica | `ApqmQueueStore` — FIFO en memoria |
| Ítem de cola | `QueueItemRecord` — inmutable, aislado por `process_id` |
| Contexto | `QueueItemContext` — proyecto, cotización, documentos, requerimiento |
| Profundidad máxima | `max_queue_depth` desde configuración centralizada |

## Ciclo de vida del procesamiento

| Etapa APQM | Descripción |
|------------|-------------|
| `solicitud_recibida` | Solicitud aceptada desde ECG |
| `solicitud_en_cola` | Encolada para procesamiento |
| `solicitud_asignada` | Worker asignado |
| `procesamiento_iniciado` | Inicio de ejecución |
| `procesamiento_en_ejecucion` | Ejecución vía PIO |
| `procesamiento_completado` | Finalizado correctamente |
| `procesamiento_cancelado` | Cancelado (preparado) |
| `error_controlado` | Error sin interrumpir el ERP |

Estados del Motor sincronizados vía `StateManager`:
- `PROCESAMIENTO_PENDIENTE` al encolar
- `PROCESANDO` durante ejecución
- PIO gestiona transiciones posteriores

## Integración con ECG

- **Único origen**: solicitudes con `source="ecg"` en `QueueItemContext`
- **Puerto**: `EcgEnqueuePort` implementado por `AsyncProcessingQueueManager`
- **Vinculación**: `service.initialize()` → `ecg.gateway.bind_enqueue(apqm.manager)`

## Integración con PIO

- APQM **nunca** inicia procesos por cuenta propia
- Ejecución exclusiva vía `ApqmExecutionPort` → `EnterpriseIntegrationApqmExecutor` → `service.start_analysis()` → PIO

## Reglas de aislamiento

1. Cada `QueueItemRecord` conserva su propio contexto inmutable
2. Índice por `process_id` — nunca mezclar procesos
3. Metadatos, documentos y requerimiento copiados al encolar
4. Historial de transiciones independiente por ítem

## Observabilidad

Cada ítem registra:
- `created_at`, `started_at`, `completed_at`, `duration_seconds`
- Historial de transiciones (`ApqmStageTransition`)
- Eventos en `EventManager` (encolado, asignación, inicio, finalización, error)

## Puntos de extensión futuros

- Múltiples workers distribuidos
- Colas con prioridades
- Reintentos automáticos (FTRRF — 8.6)
- Recuperación automática
- Balanceo de carga
- Procesamiento distribuido

El núcleo (`AsyncProcessingQueueManager`, `ApqmQueueStore`, puertos) permanece estable.
