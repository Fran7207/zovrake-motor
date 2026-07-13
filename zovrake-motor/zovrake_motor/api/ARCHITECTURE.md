# API de Integración Pública — Arquitectura Definitiva (Implementación 9.4)

## Propósito

Definir e implementar la arquitectura definitiva que integra:

```
ERP ZOVRAKE  →  API REST Oficial  →  Motor Inteligente ZOVRAKE
```

Ambos sistemas trabajan como una sola plataforma sin perder independencia.
La Implementación **9.4** certifica el flujo E2E completo ERP ↔ API ↔ Motor.
Ver `CERTIFICATION.md` y `python certify_integration_api_e2e.py`.

## Principios permanentes

- Arquitectura desacoplada
- Bajo acoplamiento / alta cohesión
- Modularidad y escalabilidad
- Trazabilidad y mantenibilidad
- Seguridad y consistencia
- Extensibilidad y separación de responsabilidades

## Arquitectura general

```
Proveedor
  ↓
Submódulo Cotizaciones
  ↓
Centro de Evidencias
  ↓
Botón Analizar Cotizaciones
  ↓
API REST Oficial (FastAPI — zovrake_motor.api.http)   ← PM9.2
  ↓
IntegrationApiService (contrato público v1)
  ↓
ERP Communication Gateway (ECG)                       ← PM8 (congelado)
  ↓
Internal Integration API
  ↓
Integration Coordinator
  ↓
Pipeline Integration Orchestrator
  ↓
Asynchronous Processing & Queue Manager
  ↓
Motor Inteligente
  ↓
Coordinator → Módulos Inteligentes
  ↓
Resultado del Análisis Inteligente
  ↓
API REST Oficial
  ↓
ERP → Cuadro Comparativo → Usuario
```

## Separación de responsabilidades

| Sistema | Puede | No puede |
|---------|-------|----------|
| **ERP** | Administrar evidencias, cargar documentos, enviar contexto, iniciar análisis, consultar estado, recibir y representar resultado | Interpretar documentos, ejecutar IA, clasificar, generar cuadros, decidir |
| **API REST** | Recibir solicitudes HTTP, validar estructura, delegar a IntegrationApiService, devolver sobre uniforme, registrar eventos | Interpretar documentos, ejecutar IA, modificar ERP, bypassear ECG |
| **IntegrationApiService** | Validar contrato público, traducir a ECG, devolver respuestas estructuradas | Ejecutar inteligencia, modificar ERP |
| **Motor** | Recibir, validar, coordinar, ejecutar módulos, generar y devolver resultados | Modificar ERP, generar UI, acceder al frontend |

## Capas

| Capa | Paquete | Estado |
|------|---------|--------|
| Transporte HTTP REST | `api.http` | **Implementado (9.2)** |
| Bootstrap runtime | `api.bootstrap` | **Implementado (9.2)** |
| Contrato público ERP ↔ API | `api.models` | Definido v1 |
| Fachada de servicio | `api.service.IntegrationApiService` | Operativa |
| Adaptador hacia ECG | `api.adapters.EcgGatewayAdapter` | Operativo |
| Plataforma empresarial | `enterprise_integration` | **Cerrada (PM8)** |
| Motor Inteligente | módulos PM3–PM7 | **Cerrados / inmutables** |

## Endpoints REST oficiales

| Método | Ruta | Responsabilidad |
|--------|------|-----------------|
| `POST` | `/api/v1/analyses` | Crear análisis |
| `GET` | `/api/v1/analyses/{analysis_id}` | Consultar análisis |
| `GET` | `/api/v1/analyses/{analysis_id}/status` | Consultar estado |
| `GET` | `/api/v1/analyses/{analysis_id}/result` | Obtener resultado |
| `GET` | `/api/v1/health/motor` | Disponibilidad del Motor |
| `GET` | `/api/v1/health/coordinator` | Disponibilidad del Coordinator |
| `GET` | `/api/v1/info/version` | Versión del servicio |
| `GET` | `/api/v1/info/service` | Estado del servicio |
| `GET` | `/api/v1/info/modules` | Módulos registrados (sin internals) |

## Sobre uniforme de respuesta

Toda respuesta HTTP incluye:

- `analysis_id`
- `status`
- `timestamp`
- `message`
- `success`
- `result` (cuando exista)
- `error` (cuando exista)
- `contract_version`

## Reglas de desacoplamiento

1. El ERP **nunca** importa módulos internos del Motor.
2. El Motor **nunca** conoce el frontend ni modifica el ERP.
3. La API pública **solo** habla con el Motor a través de ECG / plataforma PM8.
4. No se duplica lógica de PM8; se reutiliza `EnterpriseIntegrationService`.
5. No se mueven responsabilidades entre componentes congelados.
6. La capa HTTP **no** procesa documentos ni ejecuta análisis.

## Observabilidad

Cada solicitud HTTP registra conceptualmente:

- identificador de solicitud (`X-Request-Id`)
- hora de inicio / finalización
- duración
- código de respuesta
- eventos de ciclo de vida por `analysis_id` en `EventManager`

Sin herramientas específicas de monitoreo todavía.

## Arranque del servidor

```bash
pip install -e ".[api]"
python run_api_server.py --host 0.0.0.0 --port 8000
# o
zovrake-motor-api --port 8000
```

Documentación interactiva: `/api/v1/docs`

## Compatibilidad de plataforma

API REST consumible desde Windows, Linux, macOS, Android e iOS mediante clientes HTTP estándar.

## Estado

**Integración E2E certificada (9.4)** — plataforma operativa y preparada para evolución.
