# Certificación E2E — Integración ERP ↔ API ↔ Motor (Implementación 9.4)

## Objetivo

Validar que el flujo completo **zovrake-web → zovrake-motor → zovrake-web** funciona de extremo a extremo sin romper la arquitectura definida en PM8 y PM9.

## Flujo certificado

```
Proveedor
  → Submódulo Cotizaciones
  → Centro de Evidencias
  → Botón Analizar Cotizaciones
  → ZovrakeMotorIntegration (script.js)
  → API REST /api/v1
  → IntegrationApiService
  → ERP Communication Gateway
  → Coordinator
  → Motor Inteligente
  → Resultado estructurado
  → Cuadro Comparativo
  → Usuario
```

## Verificaciones

| Área | Qué valida |
|------|------------|
| Documentación | ARCHITECTURE, CONTRACT, LIFECYCLE, CERTIFICATION |
| Gobierno PM9.4 | Implementación, PM8 inmutable, flujo ERP |
| Cliente ERP | `ZovrakeMotorIntegration` en script.js |
| Flujo E2E | POST análisis → cola → estado → resultado |
| Salud API | Motor y Coordinator operativos |
| Contrato uniforme | `ApiResponseEnvelope` v1 |
| Robustez | Solicitudes inválidas → errores controlados |
| Concurrencia | Identificadores únicos por solicitud |
| Aislamiento | HTTP no importa módulos inteligentes |

## Ejecución

```bash
python certify_integration_api_e2e.py
pytest tests/certification/test_integration_api_e2e_certification.py -q
```

## Criterios de aceptación

- Documentos y contexto enviados con contrato v1
- Solicitud aceptada por la API (HTTP 202)
- Procesamiento asíncrono evidenciado
- Consultas de estado y resultado exitosas
- ERP desacoplado — solo API REST oficial
- Errores controlados sin inestabilidad

## Próxima fase

Evolución de capacidades del Motor sin rediseñar la arquitectura de integración.
