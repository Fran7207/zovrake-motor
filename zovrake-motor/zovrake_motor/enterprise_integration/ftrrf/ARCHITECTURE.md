# Fault Tolerance, Retry & Recovery Framework — Arquitectura (Implementación 8.6)

## Responsabilidad

El **Fault Tolerance, Retry & Recovery Framework (FTRRF)** es el **único componente** autorizado para detectar, registrar, clasificar y administrar fallos durante el procesamiento de solicitudes, garantizando la continuidad operativa mediante recuperación y reintentos controlados.

El ERP y el resto de procesos en ejecución nunca se ven afectados por un fallo aislado.

## Flujo de resiliencia

```
APQM.execute_item  →  ejecución vía PIO
        │
        ▼ (fallo controlado)
FaultToleranceRetryRecoveryFramework.handle_failure   [solo el APQM está autorizado]
        │
        ├─ ErrorClassifier            → categoría + severidad + recuperabilidad
        ├─ RetryPolicyRegistry        → política aplicable
        ├─ ErrorRegistryStore         → registro estructurado del error
        ├─ IntegrationContinuityPort  → coordina trazabilidad con el PIO
        │
        ▼
RecoveryOutcome (RETRY | RECOVER | CANCEL | TERMINAL_FAILURE)
        │
        ▼
APQM aplica la decisión (reintenta vía PIO o finaliza de forma controlada)
```

## Clasificación de errores

| Categoría | Recuperable | Origen típico |
|-----------|-------------|---------------|
| `error_validacion` | No | Validación estructural / contrato |
| `error_documental` | No | Documentos del Centro de Evidencias |
| `error_comunicacion` | Sí | API interna / coordinación |
| `error_procesamiento` | Sí | Operación no ejecutada |
| `error_temporal` | Sí | Timeouts / transitorios |
| `error_permanente` | No | Fallo irrecuperable |
| `error_interno_sistema` | No | Estado interno inconsistente |

El clasificador es determinístico (código de error + descripción). **No resuelve** errores automáticamente.

## Políticas de reintento

`RetryPolicyRegistry` mantiene una política por categoría:
- `max_retries`, `interval_seconds`, `strategy`, `cancel_on_categories`
- Solo las categorías recuperables admiten reintentos
- Estrategias preparadas: `NONE`, `IMMEDIATE`, `FIXED_INTERVAL` (backoff avanzado se incorpora sin tocar el núcleo)

## Recuperación de procesos

`recover_process()` reanuda un proceso interrumpido preservando:
- identificador del proceso
- estado actual (vía `StateManager`)
- historial de eventos (vía `EventManager`)
- contexto del requerimiento
- trazabilidad (coordinada con el PIO)

Nunca reinicia el proceso desde cero si puede continuar de forma segura.

## Aislamiento de fallos

- `ErrorRegistryStore` indexa registros por `process_id`
- Cada `ErrorRecord` es inmutable e independiente
- Un fallo no afecta otros procesos, solicitudes, proyectos ni colas

## Registro estructurado de errores

`ErrorRecord`: `error_id`, `process_id`, `category`, `description`, `origin_component`, `severity`, `occurred_at`, `recovery_status`, `retry_count`. Sin persistencia.

## Integración

| Integración | Regla |
|-------------|-------|
| **APQM** | Único autorizado a solicitar recuperación (`requested_by="apqm"`) |
| **PIO** | Coordina continuidad/finalización vía `IntegrationContinuityPort` |
| **Configuración** | `FaultToleranceRetryRecoveryFrameworkSettings` centralizada |
| **Estados** | Solo `MotorState` oficiales (`ERROR_VALIDACION`, `ERROR_INTERNO`, `PROCESANDO`) |
| **Eventos** | `FtrrfEventRecorder` → `EventManager` |

## Estados registrados (ciclo de resiliencia)

`fallo_detectado` → `recuperacion_iniciada` → (`reintento_programado` | `recuperacion_completada`) → (`proceso_cancelado` | `finalizacion_por_error`)

Estos son **etapas de observabilidad** del FTRRF; el estado oficial del proceso se sincroniza exclusivamente con `MotorState`.

## Observabilidad

`observability_snapshot()`: total de errores, conteo por categoría y por estado de recuperación. Cada registro incluye reintentos y tiempos.

## Puntos de extensión futuros (sin modificar el núcleo)

- Backoff exponencial
- Circuit breakers
- Dead letter queues
- Recuperación distribuida / failover
- Monitoreo distribuido

El núcleo (`FaultToleranceRetryRecoveryFramework`, clasificador, políticas, registro) permanece estable; las capacidades avanzadas se conectan mediante puertos y configuración.
