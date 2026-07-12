# ERP Communication Gateway — Arquitectura (Implementación 8.4)

## Responsabilidad

El **ERP Communication Gateway (ECG)** es el **único componente** autorizado para intercambiar información entre el ERP (Centro de Evidencias — submódulo Cotizaciones) y el Motor Inteligente.

Ningún otro módulo del ERP ni del Motor puede establecer comunicación directa entre ambos sistemas.

## Flujo de comunicación

```
Centro de Evidencias (ERP)
        │
        ▼
EvidenceCenterAnalysisRequest  (contrato ERP v1)
        │
        ▼
ErpCommunicationGateway
        │  transformación → StartAnalysisRequest (API Interna v1)
        ▼
EnterpriseIntegrationEcgDispatcher
        │
        ▼
Enterprise Integration Coordinator
        │
        ▼
Pipeline Integration Orchestrator (PIO)
        │
        ▼
Internal Integration API
        │
        ▼
Motor Inteligente (preparado — sin ejecución en 8.4)
        │
        ▼  respuesta inmutable
ErpDeliveryBuilder → ErpAnalysisDelivery
        │
        ▼
Centro de Evidencias (ERP)
```

## Contratos utilizados

| Dirección | Contrato | Versión |
|-----------|----------|---------|
| ERP → ECG | `EvidenceCenterAnalysisRequest` | v1 |
| ERP → ECG | `EvidenceCenterStatusQuery` | v1 |
| ERP → ECG | `EvidenceCenterResultQuery` | v1 |
| ECG → ERP | `ErpAnalysisDelivery` | v1 |
| ECG → PIO | `StartAnalysisRequest`, `AnalysisStatusQueryRequest`, `AnalysisResultQueryRequest` | Internal API v1 |

## Integración con la API Interna

- Toda solicitud ERP se transforma mediante `ErpRequestTransformer` al contrato oficial de la API Interna.
- Nunca se envían estructuras improvisadas ni diccionarios ad hoc.
- Las respuestas se reciben sin interpretación y se entregan al ERP mediante `ErpDeliveryBuilder`.

## Integración con el Pipeline Integration Orchestrator

- El despacho hacia el Motor **obliga** el paso por Coordinator → PIO → Internal API.
- `EnterpriseIntegrationEcgDispatcher` delega en `EnterpriseIntegrationService.start_analysis()` (y consultas equivalentes), garantizando el pipeline determinístico del PIO.
- La trazabilidad del pipeline se incluye en `TraceabilityDeliveryBundle` sin modificación.

## Reglas de desacoplamiento

1. El ERP **nunca** conoce módulos internos del Motor (`intelligent_analysis`, `comprehension`, etc.).
2. El Motor **nunca** accede a componentes internos del ERP ni al frontend.
3. El ECG **no importa** módulos de negocio del Motor; solo contratos de la API Interna y el adaptador de despacho.
4. Toda comunicación pasa por el ECG como punto de entrada/salida oficial.

## Reglas de inmutabilidad

- Los contratos ERP (`EvidenceCenterAnalysisRequest`, `ErpAnalysisDelivery`) son **frozen dataclasses**.
- `ErpDeliveryBuilder` **no modifica** recomendaciones, explicaciones, evidencias, nivel de confianza ni trazabilidad.
- Los metadatos del Motor se copian preservando `source_data_preserved=True`.

## Gestión de mensajes

- `EcgMessageStore`: almacenamiento en memoria de solicitudes, respuestas y errores.
- `EcgMessageEnvelope`: sobre inmutable con tipo, dirección y payload serializado.
- Sin colas de procesamiento en 8.4 (preparado para APQM en 8.5).

## Sistemas centralizados

| Sistema | Uso en ECG |
|---------|------------|
| Configuración | `ErpCommunicationGatewaySettings` vía `ConfigurationProvider` |
| Estados | `StateManager.create_process()` al recibir solicitud ERP |
| Eventos | `EcgEventRecorder` → `EventManager` |

## Punto de entrada oficial

```python
service.submit_evidence_center_analysis(request)
service.query_evidence_center_status(query)
service.query_evidence_center_result(query)
```

## Extensiones futuras (sin modificar el núcleo)

- HTTP / FastAPI / WebSocket (capa de transporte externa)
- Autenticación y autorización
- Cifrado de comunicación
- Balanceo de carga
- Colas asíncronas (APQM — Implementación 8.5)
- Monitoreo de tráfico

El núcleo (`ErpCommunicationGateway`, transformadores, contratos) permanece estable; las extensiones se conectan mediante puertos (`EcgIntegrationDispatchPort`) y configuración centralizada.
