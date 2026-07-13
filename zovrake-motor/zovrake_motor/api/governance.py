"""
Gobierno arquitectónico de la API de Integración Pública.

Implementación 9.3 — Integración operativa ERP ↔ API REST ↔ Motor.
"""

from __future__ import annotations

from typing import Any

PROMPT_MAESTRO_9_STATUS = "OPEN"
IMPLEMENTATION = "9.4"
PROMPT_MAESTRO_REFERENCE = "9"
NEXT_IMPLEMENTATION = None
E2E_CERTIFICATION_STATUS = "APPROVED"

PUBLIC_CONTRACT_NAME = "PublicIntegrationApi"
PUBLIC_CONTRACT_VERSION = "v1"
OFFICIAL_ERP_ENTRY_POINT = "Centro de Evidencias — Cotizaciones"
OFFICIAL_ERP_TRIGGER = "Analizar Cotizaciones"
DOWNSTREAM_CHANNEL = "ErpCommunicationGateway"
DOWNSTREAM_PLATFORM = "enterprise_integration"

RESPONSIBILITY_BOUNDARIES: tuple[dict[str, str], ...] = (
    {
        "system": "erp",
        "may": (
            "administrar Centro de Evidencias; cargar documentos; enviar contexto; "
            "iniciar análisis; consultar estado; recibir resultado; representar visualmente"
        ),
        "must_not": (
            "interpretar documentos; ejecutar algoritmos inteligentes; "
            "clasificar; generar cuadros comparativos; tomar decisiones"
        ),
    },
    {
        "system": "integration_api",
        "may": (
            "exponer contrato público; validar sobre de solicitud; "
            "traducir a ECG; devolver respuestas estructuradas; registrar eventos API"
        ),
        "must_not": (
            "ejecutar inteligencia; modificar ERP; acceder al frontend; "
            "bypassear ECG o Internal Integration API"
        ),
    },
    {
        "system": "motor",
        "may": (
            "recibir solicitudes; validar; coordinar; ejecutar módulos; "
            "generar resultados; devolver respuestas estructuradas"
        ),
        "must_not": "modificar el ERP; generar interfaz gráfica; acceder al frontend",
    },
)

OFFICIAL_INTEGRATION_FLOW: tuple[str, ...] = (
    "Proveedor",
    "Submodulo Cotizaciones",
    "Centro de Evidencias",
    "Boton Analizar Cotizaciones",
    "API de Integracion",
    "ERP Communication Gateway",
    "Internal Integration API",
    "Integration Coordinator",
    "Pipeline Integration Orchestrator",
    "Asynchronous Processing & Queue Manager",
    "Motor Inteligente",
    "Coordinator",
    "Modulos Inteligentes",
    "Resultado del Analisis Inteligente",
    "API de Integracion",
    "ERP",
    "Cuadro Comparativo",
    "Usuario",
)

REST_ENDPOINTS: tuple[str, ...] = (
    "POST /api/v1/analyses",
    "GET /api/v1/analyses/{analysis_id}",
    "GET /api/v1/analyses/{analysis_id}/status",
    "GET /api/v1/analyses/{analysis_id}/result",
    "GET /api/v1/health/motor",
    "GET /api/v1/health/coordinator",
    "GET /api/v1/info/version",
    "GET /api/v1/info/service",
    "GET /api/v1/info/modules",
)

ERP_INTEGRATION_FLOW: tuple[str, ...] = (
    "Logistica",
    "Submodulo Cotizaciones",
    "Centro de Evidencias",
    "Boton Analizar Cotizaciones",
    "ZovrakeMotorIntegration (cliente HTTP ERP)",
    "API REST Oficial",
    "IntegrationApiService",
    "ERP Communication Gateway",
    "Coordinator",
    "Motor Inteligente",
    "Resultado Estructurado",
    "Cuadro Comparativo",
    "Usuario",
)

EXTENSION_POINTS_AFTER_9_4: tuple[str, ...] = (
    "authentication_enforcement",
    "authorization_enforcement",
    "webhook_notifications",
    "performance_tuning",
)


def governance_snapshot() -> dict[str, Any]:
    return {
        "prompt_maestro": PROMPT_MAESTRO_REFERENCE,
        "status": PROMPT_MAESTRO_9_STATUS,
        "implementation": IMPLEMENTATION,
        "next_implementation": NEXT_IMPLEMENTATION,
        "public_contract": {
            "name": PUBLIC_CONTRACT_NAME,
            "version": PUBLIC_CONTRACT_VERSION,
            "official_erp_entry_point": OFFICIAL_ERP_ENTRY_POINT,
            "official_erp_trigger": OFFICIAL_ERP_TRIGGER,
            "downstream_channel": DOWNSTREAM_CHANNEL,
            "downstream_platform": DOWNSTREAM_PLATFORM,
        },
        "responsibility_boundaries": list(RESPONSIBILITY_BOUNDARIES),
        "official_integration_flow": list(OFFICIAL_INTEGRATION_FLOW),
        "rest_endpoints": list(REST_ENDPOINTS),
        "erp_integration_flow": list(ERP_INTEGRATION_FLOW),
        "e2e_certification": {
            "status": E2E_CERTIFICATION_STATUS,
            "implementation": IMPLEMENTATION,
            "official_entry_point": OFFICIAL_ERP_ENTRY_POINT,
            "official_trigger": OFFICIAL_ERP_TRIGGER,
        },
        "extension_points_after_9_4": list(EXTENSION_POINTS_AFTER_9_4),
        "pm8_unchanged": True,
        "erp_unchanged": True,
        "motor_internals_unchanged": True,
    }
