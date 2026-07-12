"""Registro extensible de componentes del Módulo de Integración Empresarial."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.async_processing_queue_manager import (
    AsyncProcessingQueueManagerComponent,
)
from zovrake_motor.enterprise_integration.components.api_gateway_internal import ApiGatewayInternal
from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.components.communication_contracts import (
    CommunicationContracts,
)
from zovrake_motor.enterprise_integration.components.erp_communication_gateway import (
    ErpCommunicationGatewayComponent,
)
from zovrake_motor.enterprise_integration.components.error_management_framework import (
    ErrorManagementFramework,
)
from zovrake_motor.enterprise_integration.components.fault_tolerance_retry_recovery_framework import (
    FaultToleranceRetryRecoveryFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.integration_configuration_manager import (
    IntegrationConfigurationManager,
)
from zovrake_motor.enterprise_integration.components.integration_event_manager import (
    IntegrationEventManager,
)
from zovrake_motor.enterprise_integration.components.integration_traceability_manager import (
    IntegrationTraceabilityManager,
)
from zovrake_motor.enterprise_integration.components.pipeline_integration_orchestrator import (
    PipelineIntegrationOrchestratorComponent,
)
from zovrake_motor.enterprise_integration.components.process_status_manager import (
    ProcessStatusManager,
)
from zovrake_motor.enterprise_integration.components.observability_metrics_monitoring_framework import (
    ObservabilityMetricsMonitoringFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.performance_optimization_scalability_framework import (
    PerformanceOptimizationScalabilityFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.security_validation_audit_framework import (
    SecurityValidationAuditFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.request_dispatcher import RequestDispatcher
from zovrake_motor.enterprise_integration.components.response_dispatcher import ResponseDispatcher

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.components.enterprise_integration_coordinator import (
        EnterpriseIntegrationCoordinator,
    )
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class ComponentRegistry:
    """
    Registro de componentes del Módulo de Integración Empresarial.

    Permite incorporar nuevos mecanismos de integración mediante extensión
    sin modificar el núcleo.
    """

    def __init__(self) -> None:
        self._components: dict[str, EnterpriseIntegrationComponentPort] = {}

    def register(self, component: EnterpriseIntegrationComponentPort) -> None:
        self._components[component.component_name] = component

    def register_defaults(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
    ) -> EnterpriseIntegrationCoordinator:
        """Registra la estructura base de componentes preparada para PM8."""
        from zovrake_motor.enterprise_integration.components.enterprise_integration_coordinator import (
            EnterpriseIntegrationCoordinator,
        )

        components: tuple[EnterpriseIntegrationComponentPort, ...] = (
            ErpCommunicationGatewayComponent(integration=integration),
            AsyncProcessingQueueManagerComponent(integration=integration),
            FaultToleranceRetryRecoveryFrameworkComponent(integration=integration),
            SecurityValidationAuditFrameworkComponent(integration=integration),
            ObservabilityMetricsMonitoringFrameworkComponent(integration=integration),
            PerformanceOptimizationScalabilityFrameworkComponent(integration=integration),
            ApiGatewayInternal(integration=integration),
            PipelineIntegrationOrchestratorComponent(integration=integration),
            RequestDispatcher(),
            ResponseDispatcher(),
            ProcessStatusManager(),
            ErrorManagementFramework(),
            CommunicationContracts(registry=self),
            IntegrationEventManager(),
            IntegrationTraceabilityManager(),
            IntegrationConfigurationManager(),
        )

        for component in components:
            self.register(component)

        coordinator = EnterpriseIntegrationCoordinator(self, integration=integration)
        self.register(coordinator)
        return coordinator

    def get(self, name: str) -> EnterpriseIntegrationComponentPort | None:
        return self._components.get(name)

    def all_components(self) -> tuple[EnterpriseIntegrationComponentPort, ...]:
        return tuple(self._components.values())

    def count(self) -> int:
        return len(self._components)

    def ready_count(self) -> int:
        return sum(1 for component in self._components.values() if component.is_ready())

    def snapshot(self) -> list[dict[str, Any]]:
        return [component.snapshot() for component in self._components.values()]
