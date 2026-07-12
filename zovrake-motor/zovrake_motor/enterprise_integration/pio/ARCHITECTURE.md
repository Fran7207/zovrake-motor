# Pipeline Integration Orchestrator — Arquitectura (Implementación 8.3)

## Responsabilidad

El **Pipeline Integration Orchestrator (PIO)** es el único componente responsable de coordinar el ciclo completo de una solicitud entre el ERP y el Motor Inteligente. No contiene lógica de negocio, no ejecuta IA y no conoce la implementación interna del Motor.

## Flujo oficial

```
ERP
 ↓
Internal Integration API
 ↓
Integration Coordinator
 ↓
Pipeline Integration Orchestrator (PIO)
 ↓
Motor Inteligente (unidad abstracta — MotorUnitGateway)
 ↓
PIO
 ↓
Internal Integration API
 ↓
ERP
```

## Fases del Pipeline (determinísticas)

| Fase | Descripción |
|------|-------------|
| `solicitud_recibida` | Recepción de la solicitud |
| `validacion_iniciada` | Validación estructural vía API Interna |
| `solicitud_aceptada` | Solicitud aceptada |
| `procesamiento_iniciado` | Inicio preparado del procesamiento |
| `invocacion_motor_preparada` | Invocación del Motor como unidad única |
| `procesamiento_en_ejecucion` | Seguimiento (sin ejecución en 8.3) |
| `resultado_generado` | Resultado estructurado preparado |
| `resultado_entregado` | Entrega al canal de respuesta |
| `proceso_finalizado` | Cierre del ciclo |
| `error_controlado` | Error controlado del Pipeline |

Ninguna fase puede ejecutarse fuera del orden definido por operación.

## Integración con sistemas centralizados

- **Configuración**: `PipelineIntegrationOrchestratorSettings`
- **Estados**: transiciones vía `StateManager` usando estados oficiales existentes
- **Eventos**: `PipelineEventRecorder` → `EventManager`

## Trazabilidad

Cada solicitud mantiene durante todo el Pipeline:

- `process_id`, `project_id`, `analysis_id`
- fase actual e historial de transiciones
- marcas de tiempo
- metadatos de invocación del Motor (preparada, no ejecutada)

## Puntos de extensión futuros

- Procesamiento asíncrono (`async_processing_prepared`)
- Reintentos (`retry_prepared`)
- Cancelación avanzada (`cancellation_prepared`)
- Colas de trabajo y procesamiento distribuido

## Próxima implementación

**8.4 — ERP Communication Gateway (ECG)**: canal oficial entre Centro de Evidencias del ERP y el Módulo de Integración.
