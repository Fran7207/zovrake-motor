"""Componente Performance Optimization & Scalability Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.posf.framework import (
    PerformanceOptimizationScalabilityFramework,
)

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class PerformanceOptimizationScalabilityFrameworkComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del POSF.

    Ningún otro componente asume optimización de rendimiento ni escalabilidad.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        framework: PerformanceOptimizationScalabilityFramework | None = None,
    ) -> None:
        if integration is None and framework is None:
            raise ValueError("Se requiere integration o framework")
        self._framework = framework or PerformanceOptimizationScalabilityFramework(
            integration=integration,  # type: ignore[arg-type]
        )

    @property
    def component_name(self) -> str:
        return "performance_optimization_scalability_framework"

    @property
    def component_label(self) -> str:
        return "Performance Optimization & Scalability Framework"

    @property
    def framework(self) -> PerformanceOptimizationScalabilityFramework:
        return self._framework

    def initialize(self) -> None:
        self._framework.initialize()

    def is_ready(self) -> bool:
        return self._framework.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["framework"] = self._framework.snapshot()
        return base
