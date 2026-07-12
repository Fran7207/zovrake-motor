# Observability, Metrics & Monitoring Framework (OMMF)

## Responsabilidad

Componente transversal **único** responsable de recopilar métricas, trazas, indicadores de rendimiento y estados operativos del flujo de integración ERP ↔ Motor Inteligente.

No altera el flujo operativo. No implementa herramientas externas (Prometheus, Grafana, OpenTelemetry, etc.).

## Arquitectura

```
ECG → SVAF → APQM → FTRRF → Coordinator → PIO → Internal API → Motor
         ↑         ↑         ↑              ↑
         └─────────┴─────────┴──────────────┴── OMMF (observación transversal)
```

### Componentes internos

| Componente | Responsabilidad |
|---|---|
| `MetricsCollector` | Contadores operativos (solicitudes, éxitos, fallos, reintentos, validaciones, auditorías) |
| `TraceCollector` | Trazas con continuidad por `process_id` / `trace_id` |
| `PerformanceTracker` | Tiempos de validación, cola, procesamiento, recuperación |
| `HealthMonitor` | Estado operativo por componente (disponible, ocupado, degradado, etc.) |
| `OmmfEventRecorder` | Eventos al Sistema Centralizado de Eventos |

## Integraciones

| Componente | Hook | Datos registrados |
|---|---|---|
| **PIO** | `bind_observability()` en `_advance_phase` | Transiciones de fase, duración, continuidad de traza |
| **APQM** | `bind_observability()` en enqueue/ejecución | Cola, pendientes, activos, finalizados |
| **FTRRF** | `bind_observability()` en fallos/recuperación | Errores, reintentos, recuperaciones, fallos permanentes |
| **SVAF** | `bind_observability()` en validación/auditoría | Validaciones aprobadas/rechazadas, auditorías |

## Métricas recopiladas

- `requests_received`, `requests_processed`
- `processes_successful`, `processes_failed`, `processes_cancelled`, `processes_recovered`
- `retries_executed`, `validations_performed`, `audits_recorded`

## Modelo de trazabilidad

Cada span conserva: `process_id`, `project_id`, `quotation_id`, `component`, `pipeline_phase`, `started_at`, `duration_ms`. El `trace_id` se mantiene constante por proceso.

## Puntos de extensión futuros

Flags de configuración preparados para: OpenTelemetry, Prometheus, Grafana, Elastic Stack, Jaeger, Zipkin, dashboards, alertas automáticas y monitoreo distribuido — sin modificar el núcleo del OMMF.
