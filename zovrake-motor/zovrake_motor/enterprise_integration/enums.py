"""Enumeraciones del Módulo de Integración Empresarial."""

from __future__ import annotations

from enum import Enum


class EnterpriseIntegrationComponentType(str, Enum):
    """Componentes internos del módulo de Integración Empresarial."""

    ENTERPRISE_INTEGRATION_COORDINATOR = "enterprise_integration_coordinator"
    API_GATEWAY_INTERNAL = "api_gateway_internal"
    REQUEST_DISPATCHER = "request_dispatcher"
    RESPONSE_DISPATCHER = "response_dispatcher"
    PROCESS_STATUS_MANAGER = "process_status_manager"
    ERROR_MANAGEMENT_FRAMEWORK = "error_management_framework"
    COMMUNICATION_CONTRACTS = "communication_contracts"
    INTEGRATION_EVENT_MANAGER = "integration_event_manager"
    INTEGRATION_TRACEABILITY_MANAGER = "integration_traceability_manager"
    INTEGRATION_CONFIGURATION_MANAGER = "integration_configuration_manager"
    PIPELINE_INTEGRATION_ORCHESTRATOR = "pipeline_integration_orchestrator"
    ERP_COMMUNICATION_GATEWAY = "erp_communication_gateway"
    ASYNC_PROCESSING_QUEUE_MANAGER = "async_processing_queue_manager"
    FAULT_TOLERANCE_RETRY_RECOVERY_FRAMEWORK = "fault_tolerance_retry_recovery_framework"
    SECURITY_VALIDATION_AUDIT_FRAMEWORK = "security_validation_audit_framework"
    OBSERVABILITY_METRICS_MONITORING_FRAMEWORK = "observability_metrics_monitoring_framework"
    PERFORMANCE_OPTIMIZATION_SCALABILITY_FRAMEWORK = "performance_optimization_scalability_framework"


class EnterpriseIntegrationPhase(str, Enum):
    """Fases preparadas del flujo de integración empresarial."""

    PREPARACION = "preparacion"
    CONSUMO_RESULTADO_ANALISIS_INTELIGENTE = "consumo_resultado_analisis_inteligente"
    API_INTERNA = "api_interna"
    ENVIO_SOLICITUD = "envio_solicitud"
    RECEPCION_RESPUESTA = "recepcion_respuesta"
    GESTION_ESTADO_PROCESO = "gestion_estado_proceso"
    GESTION_ERRORES = "gestion_errores"
    GESTION_CONTRATOS = "gestion_contratos"
    GESTION_EVENTOS_INTEGRACION = "gestion_eventos_integracion"
    GESTION_TRAZABILIDAD_INTEGRACION = "gestion_trazabilidad_integracion"
    GESTION_CONFIGURACION_INTEGRACION = "gestion_configuracion_integracion"
    FINALIZACION = "finalizacion"
