"""Configuración del Módulo de Integración Empresarial."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ErpCommunicationGatewaySettings:
    """Configuración del ERP Communication Gateway — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True
    evidence_center_integration_prepared: bool = True
    immutability_enforced: bool = True
    http_transport_prepared: bool = True
    queue_processing_prepared: bool = True
    authentication_prepared: bool = True

    @classmethod
    def default(cls) -> ErpCommunicationGatewaySettings:
        return cls()


@dataclass(frozen=True)
class AsyncProcessingQueueManagerSettings:
    """Configuración del APQM — fuente centralizada."""

    enabled: bool = True
    prepared: bool = True
    in_memory_queue_prepared: bool = True
    worker_prepared: bool = True
    max_queue_depth: int = 10_000
    max_concurrent_workers: int = 10
    auto_start_worker: bool = False
    priority_prepared: bool = True
    retry_prepared: bool = True
    distributed_processing_prepared: bool = True
    load_balancing_prepared: bool = True

    @classmethod
    def default(cls) -> AsyncProcessingQueueManagerSettings:
        return cls()


@dataclass(frozen=True)
class FaultToleranceRetryRecoveryFrameworkSettings:
    """Configuración del FTRRF — fuente centralizada."""

    enabled: bool = True
    prepared: bool = True
    error_classification_prepared: bool = True
    retry_policies_prepared: bool = True
    default_max_retries: int = 3
    default_retry_interval_seconds: float = 0.0
    recovery_prepared: bool = True
    process_isolation_enforced: bool = True
    circuit_breaker_prepared: bool = True
    dead_letter_queue_prepared: bool = True
    backoff_prepared: bool = True
    distributed_recovery_prepared: bool = True

    @classmethod
    def default(cls) -> FaultToleranceRetryRecoveryFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class SecurityValidationAuditFrameworkSettings:
    """Configuración del SVAF — fuente centralizada."""

    enabled: bool = True
    prepared: bool = True
    validation_engine_prepared: bool = True
    integrity_validation_prepared: bool = True
    audit_framework_prepared: bool = True
    oauth_prepared: bool = True
    jwt_prepared: bool = True
    rbac_prepared: bool = True
    digital_signature_prepared: bool = True
    end_to_end_encryption_prepared: bool = True
    distributed_audit_prepared: bool = True

    @classmethod
    def default(cls) -> SecurityValidationAuditFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class ObservabilityMetricsMonitoringFrameworkSettings:
    """Configuración del OMMF — fuente centralizada."""

    enabled: bool = True
    prepared: bool = True
    metrics_collector_prepared: bool = True
    trace_collector_prepared: bool = True
    performance_tracker_prepared: bool = True
    health_monitor_prepared: bool = True
    opentelemetry_prepared: bool = True
    prometheus_prepared: bool = True
    grafana_prepared: bool = True
    elastic_stack_prepared: bool = True
    jaeger_prepared: bool = True
    zipkin_prepared: bool = True
    distributed_monitoring_prepared: bool = True

    @classmethod
    def default(cls) -> ObservabilityMetricsMonitoringFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class PerformanceOptimizationScalabilityFrameworkSettings:
    """Configuración del POSF — fuente centralizada."""

    enabled: bool = True
    prepared: bool = True
    pipeline_optimization_prepared: bool = True
    resource_optimization_prepared: bool = True
    async_optimization_prepared: bool = True
    reuse_registry_prepared: bool = True
    queue_congestion_threshold: int = 100
    horizontal_scaling_prepared: bool = True
    vertical_scaling_prepared: bool = True
    load_balancing_prepared: bool = True
    auto_scaling_prepared: bool = True
    multi_node_prepared: bool = True
    kubernetes_prepared: bool = True
    multi_datacenter_prepared: bool = True
    container_orchestration_prepared: bool = True

    @classmethod
    def default(cls) -> PerformanceOptimizationScalabilityFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class PipelineIntegrationOrchestratorSettings:
    """Configuración del PIO — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True
    deterministic_pipeline: bool = True
    async_processing_prepared: bool = True
    retry_prepared: bool = True
    cancellation_prepared: bool = True

    @classmethod
    def default(cls) -> PipelineIntegrationOrchestratorSettings:
        return cls()


@dataclass(frozen=True)
class InternalIntegrationApiSettings:
    """Configuración de la API Interna del Motor — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True
    active_contract_version: str = "v1"
    contract_versioning_prepared: bool = True
    structural_validation_enabled: bool = True

    @classmethod
    def default(cls) -> InternalIntegrationApiSettings:
        return cls()


@dataclass(frozen=True)
class ApiGatewayInternalSettings:
    """Configuración del API Gateway Interno — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> ApiGatewayInternalSettings:
        return cls()


@dataclass(frozen=True)
class RequestDispatcherSettings:
    """Configuración del Request Dispatcher — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> RequestDispatcherSettings:
        return cls()


@dataclass(frozen=True)
class ResponseDispatcherSettings:
    """Configuración del Response Dispatcher — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> ResponseDispatcherSettings:
        return cls()


@dataclass(frozen=True)
class ProcessStatusManagerSettings:
    """Configuración del Process Status Manager — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> ProcessStatusManagerSettings:
        return cls()


@dataclass(frozen=True)
class ErrorManagementFrameworkSettings:
    """Configuración del Error Management Framework — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> ErrorManagementFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class CommunicationContractsSettings:
    """Configuración de Communication Contracts — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> CommunicationContractsSettings:
        return cls()


@dataclass(frozen=True)
class IntegrationEventManagerSettings:
    """Configuración del Integration Event Manager — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> IntegrationEventManagerSettings:
        return cls()


@dataclass(frozen=True)
class IntegrationTraceabilityManagerSettings:
    """Configuración del Integration Traceability Manager — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> IntegrationTraceabilityManagerSettings:
        return cls()


@dataclass(frozen=True)
class IntegrationConfigurationManagerSettings:
    """Configuración del Integration Configuration Manager — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> IntegrationConfigurationManagerSettings:
        return cls()


@dataclass(frozen=True)
class EnterpriseIntegrationSettings:
    """
    Configuración de Integración Empresarial — fuente centralizada.

    Sin activar integración completa en esta etapa.
    """

    enabled: bool = False
    max_requests_per_process: int = 5_000
    max_concurrent_integrations: int = 1_000
    intelligent_analysis_integration_prepared: bool = True
    intelligent_analysis_enabled: bool = False
    pm8_input_contract_required: bool = True
    erp_communication_gateway: ErpCommunicationGatewaySettings = field(
        default_factory=ErpCommunicationGatewaySettings.default,
    )
    async_processing_queue_manager: AsyncProcessingQueueManagerSettings = field(
        default_factory=AsyncProcessingQueueManagerSettings.default,
    )
    fault_tolerance_retry_recovery_framework: FaultToleranceRetryRecoveryFrameworkSettings = field(
        default_factory=FaultToleranceRetryRecoveryFrameworkSettings.default,
    )
    security_validation_audit_framework: SecurityValidationAuditFrameworkSettings = field(
        default_factory=SecurityValidationAuditFrameworkSettings.default,
    )
    observability_metrics_monitoring_framework: ObservabilityMetricsMonitoringFrameworkSettings = field(
        default_factory=ObservabilityMetricsMonitoringFrameworkSettings.default,
    )
    performance_optimization_scalability_framework: PerformanceOptimizationScalabilityFrameworkSettings = field(
        default_factory=PerformanceOptimizationScalabilityFrameworkSettings.default,
    )
    pipeline_integration_orchestrator: PipelineIntegrationOrchestratorSettings = field(
        default_factory=PipelineIntegrationOrchestratorSettings.default,
    )
    internal_integration_api: InternalIntegrationApiSettings = field(
        default_factory=InternalIntegrationApiSettings.default,
    )
    api_gateway_internal: ApiGatewayInternalSettings = field(
        default_factory=ApiGatewayInternalSettings.default,
    )
    request_dispatcher: RequestDispatcherSettings = field(
        default_factory=RequestDispatcherSettings.default,
    )
    response_dispatcher: ResponseDispatcherSettings = field(
        default_factory=ResponseDispatcherSettings.default,
    )
    process_status_manager: ProcessStatusManagerSettings = field(
        default_factory=ProcessStatusManagerSettings.default,
    )
    error_management_framework: ErrorManagementFrameworkSettings = field(
        default_factory=ErrorManagementFrameworkSettings.default,
    )
    communication_contracts: CommunicationContractsSettings = field(
        default_factory=CommunicationContractsSettings.default,
    )
    integration_event_manager: IntegrationEventManagerSettings = field(
        default_factory=IntegrationEventManagerSettings.default,
    )
    integration_traceability_manager: IntegrationTraceabilityManagerSettings = field(
        default_factory=IntegrationTraceabilityManagerSettings.default,
    )
    integration_configuration_manager: IntegrationConfigurationManagerSettings = field(
        default_factory=IntegrationConfigurationManagerSettings.default,
    )

    @classmethod
    def default(cls) -> EnterpriseIntegrationSettings:
        return cls()
