# API Interna del Motor Inteligente — Arquitectura (Implementación 8.2)

## Propósito

La **API Interna del Motor Inteligente** (`InternalIntegrationApi`) es el contrato oficial de comunicación entre el ERP y el Motor Inteligente. Ningún componente del ERP puede acceder directamente a los módulos internos del Motor.

## Principios

- **Contract First Design** — contratos definidos antes que la implementación
- **API First** — interfaces de servicio desacopladas
- **Arquitectura Hexagonal** — puertos e implementaciones separadas
- **Versionado** — v1 activa; v2 preparada sin ruptura
- **Sin HTTP** — no expone endpoints públicos en 8.2

## Flujo obligatorio

```
ERP
 ↓
Enterprise Integration Service
 ↓
Enterprise Integration Coordinator  ← único enrutador
 ↓
Internal Integration API (ApiGatewayInternal)
 ↓
Servicios de contrato (sin ejecución real)
```

## Contratos de solicitud (v1)

| Contrato | Operación |
|----------|-----------|
| `StartAnalysisRequest` | Iniciar análisis |
| `AnalysisStatusQueryRequest` | Consultar estado |
| `AnalysisResultQueryRequest` | Consultar resultado |
| `CancelAnalysisRequest` | Cancelar (preparado) |
| `ValidateAnalysisRequest` | Validar solicitud |

## Contratos de respuesta (v1)

| Contrato | Contenido |
|----------|-----------|
| `StartAnalysisResponse` | process_id, processing_status, timestamps |
| `AnalysisStatusResponse` | estado + motor_state (si existe) |
| `AnalysisResultResponse` | resultado estructurado preparatorio |
| `CancelAnalysisResponse` | cancelación preparada |
| `ValidateAnalysisResponse` | validación estructural |
| `InternalApiErrorResponse` | errores controlados |

## Interfaces de servicio

| Puerto | Implementación stub |
|--------|---------------------|
| `AnalysisRequestServicePort` | `AnalysisRequestService` |
| `AnalysisStatusServicePort` | `AnalysisStatusService` |
| `AnalysisResultServicePort` | `AnalysisResultService` |
| `ValidationServicePort` | `ValidationService` |
| `ErrorResponseServicePort` | `ErrorResponseService` |

## Versionado

- **Activa**: `v1`
- **Futura**: `v2` (registrada, no implementada)
- Registro: `ContractVersionRegistry`

## Integración con sistemas centralizados

- **Configuración**: `InternalIntegrationApiSettings` en `ConfigCategory.ENTERPRISE_INTEGRATION`
- **Estados**: consulta de `StateManager` en status (sin nuevos estados)
- **Eventos**: `InternalApiEventRecorder` → `EventManager`

## Validación

`StructuralValidator` verifica estructura, tipos y campos obligatorios. Sin validación funcional ni ejecución de análisis.

## Preparación futura

La API Interna está preparada para incorporar HTTP, FastAPI, autenticación, autorización, observabilidad y auditoría **sin modificar los contratos internos**.

## Próxima implementación

**8.3 — Pipeline Integration Orchestrator (PIO)**: orquestación del ciclo completo de ejecución del análisis.
