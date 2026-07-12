"""Componente Fault Tolerance, Retry & Recovery Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.ftrrf.framework import (
    FaultToleranceRetryRecoveryFramework,
)

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class FaultToleranceRetryRecoveryFrameworkComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del FTRRF.

    Ningún otro componente asume la gestión de fallos y recuperación.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        framework: FaultToleranceRetryRecoveryFramework | None = None,
    ) -> None:
        if integration is None and framework is None:
            raise ValueError("Se requiere integration o framework")
        self._framework = framework or FaultToleranceRetryRecoveryFramework(
            integration=integration,  # type: ignore[arg-type]
        )

    @property
    def component_name(self) -> str:
        return "fault_tolerance_retry_recovery_framework"

    @property
    def component_label(self) -> str:
        return "Fault Tolerance, Retry & Recovery Framework"

    @property
    def framework(self) -> FaultToleranceRetryRecoveryFramework:
        return self._framework

    def initialize(self) -> None:
        self._framework.initialize()

    def is_ready(self) -> bool:
        return self._framework.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["framework"] = self._framework.snapshot()
        base["errors"] = self._framework.error_store.snapshot()
        return base
