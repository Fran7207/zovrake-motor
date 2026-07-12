"""Componente Observability, Metrics & Monitoring Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.ommf.framework import ObservabilityMetricsMonitoringFramework

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class ObservabilityMetricsMonitoringFrameworkComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del OMMF.

    Ningún otro componente asume recopilación centralizada de observabilidad.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        framework: ObservabilityMetricsMonitoringFramework | None = None,
    ) -> None:
        if integration is None and framework is None:
            raise ValueError("Se requiere integration o framework")
        self._framework = framework or ObservabilityMetricsMonitoringFramework(
            integration=integration,  # type: ignore[arg-type]
        )

    @property
    def component_name(self) -> str:
        return "observability_metrics_monitoring_framework"

    @property
    def component_label(self) -> str:
        return "Observability, Metrics & Monitoring Framework"

    @property
    def framework(self) -> ObservabilityMetricsMonitoringFramework:
        return self._framework

    def initialize(self) -> None:
        self._framework.initialize()

    def is_ready(self) -> bool:
        return self._framework.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["framework"] = self._framework.snapshot()
        return base
