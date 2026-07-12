# Security, Validation & Audit Framework — Arquitectura (Implementación 8.7)

## Responsabilidad

El **Security, Validation & Audit Framework (SVAF)** es el **único componente** autorizado para validación estructural, verificación de integridad y auditoría del flujo de integración ERP ↔ Motor.

La seguridad se implementa como capa transversal sin invadir la lógica de negocio.

## Flujo de validación

```
Centro de Evidencias (ERP)
        ↓
ErpCommunicationGateway
        ↓
SVAF.validate_inbound_*   → rechazo → FTRRF + entrega error al ERP
        ↓ (aprobado + auditoría)
APQM / Pipeline
        ↓
PIO (authorize_pipeline_entry + validate_internal_request)
        ↓
Motor (preparado)
        ↓
SVAF.validate_outbound_delivery
        ↓
Centro de Evidencias (ERP)
```

## Arquitectura de validación

| Componente | Responsabilidad |
|------------|-----------------|
| `ValidationEngine` | Estructura, campos obligatorios, formatos, identificadores |
| `RequestIntegrityValidator` | Completitud, duplicados, estructuras inválidas |
| `SecurityValidationAuditFramework` | Orquestación, estados, eventos, métricas |

## Arquitectura de auditoría

`AuditRecord` registra: `process_id`, `operation`, `component`, `direction`, `result`, `process_state`, `errors_detected`, `occurred_at`. Almacenamiento en memoria vía `AuditStore`.

## Reglas de integridad

- No corregir mensajes automáticamente
- Detectar contratos inválidos, mensajes incompletos/duplicados, respuestas inconsistentes
- Sin mecanismos criptográficos en 8.7

## Integraciones

| Sistema | Regla |
|---------|-------|
| **ECG** | Valida inbound antes del Pipeline; outbound antes de entregar al ERP |
| **PIO** | Solo inicia procesamiento tras autorización SVAF |
| **FTRRF** | Notificado en rechazos (`requested_by="svaf"`) |
| **Configuración** | `SecurityValidationAuditFrameworkSettings` |
| **Estados** | `VALIDANDO_INFORMACION`, `INFORMACION_RECIBIDA`, `ERROR_VALIDACION` |
| **Eventos** | Validación, auditoría, integridad |

## Observabilidad

Métricas: validaciones totales/aprobadas/rechazadas, errores de integridad, auditorías registradas, duración promedio.

## Puntos de extensión futuros

OAuth 2.0, OpenID Connect, JWT, SSO, MFA, RBAC, ABAC, firmas digitales, cifrado E2E, auditoría distribuida — sin modificar el núcleo del SVAF.
