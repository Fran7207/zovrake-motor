"""Integración del módulo con configuración, estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.config.categories.enterprise_integration import EnterpriseIntegrationSettings
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class EnterpriseIntegrationMotorIntegration:
    """
    Puente de integración con infraestructura central del Motor.

    No genera eventos ni modifica estados en esta etapa.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._state_manager = state_manager or StateManager()
        self._event_manager = event_manager or EventManager()

    @property
    def config_provider(self) -> ConfigurationProvider | None:
        return self._config_provider

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    def enterprise_integration_settings(self) -> EnterpriseIntegrationSettings:
        if self._config_provider is not None:
            return self._config_provider.enterprise_integration()
        return EnterpriseIntegrationSettings.default()

    def is_enabled(self) -> bool:
        return self.enterprise_integration_settings().enabled

    def snapshot(self) -> dict[str, Any]:
        settings = self.enterprise_integration_settings()
        return {
            "enabled": settings.enabled,
            "max_requests_per_process": settings.max_requests_per_process,
            "max_concurrent_integrations": settings.max_concurrent_integrations,
            "intelligent_analysis_integration_prepared": (
                settings.intelligent_analysis_integration_prepared
            ),
            "pm8_input_contract_required": settings.pm8_input_contract_required,
            "internal_integration_api_prepared": (
                settings.internal_integration_api.prepared
            ),
            "pipeline_integration_orchestrator_prepared": (
                settings.pipeline_integration_orchestrator.prepared
            ),
            "erp_communication_gateway_prepared": (
                settings.erp_communication_gateway.prepared
            ),
            "async_processing_queue_manager_prepared": (
                settings.async_processing_queue_manager.prepared
            ),
            "fault_tolerance_retry_recovery_framework_prepared": (
                settings.fault_tolerance_retry_recovery_framework.prepared
            ),
            "security_validation_audit_framework_prepared": (
                settings.security_validation_audit_framework.prepared
            ),
            "observability_metrics_monitoring_framework_prepared": (
                settings.observability_metrics_monitoring_framework.prepared
            ),
            "performance_optimization_scalability_framework_prepared": (
                settings.performance_optimization_scalability_framework.prepared
            ),
            "state_management_ready": self._state_manager is not None,
            "event_management_ready": self._event_manager is not None,
        }
