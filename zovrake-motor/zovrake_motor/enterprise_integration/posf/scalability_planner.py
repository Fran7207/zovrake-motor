"""Planificador de escalabilidad — preparación horizontal y vertical."""

from __future__ import annotations

from typing import Any

from zovrake_motor.enterprise_integration.posf.enums import ScalabilityMode
from zovrake_motor.enterprise_integration.posf.models import ScalabilityReadiness


class ScalabilityPlanner:
    """
    Prepara la arquitectura para escalado empresarial futuro.

    No implementa sincronización distribuida ni balanceadores físicos.
    """

    def __init__(
        self,
        *,
        horizontal_prepared: bool = True,
        vertical_prepared: bool = True,
        load_balancing_prepared: bool = True,
        auto_scaling_prepared: bool = True,
        multi_node_prepared: bool = True,
    ) -> None:
        self._readiness = ScalabilityReadiness(
            mode=ScalabilityMode.ENTERPRISE_PREPARED,
            horizontal_prepared=horizontal_prepared,
            vertical_prepared=vertical_prepared,
            load_balancing_prepared=load_balancing_prepared,
            auto_scaling_prepared=auto_scaling_prepared,
            multi_node_prepared=multi_node_prepared,
        )

    @property
    def readiness(self) -> ScalabilityReadiness:
        return self._readiness

    def evaluate_capacity(
        self,
        *,
        concurrent_processes: int,
        max_concurrent_integrations: int,
    ) -> ScalabilityMode:
        if concurrent_processes >= max_concurrent_integrations:
            return ScalabilityMode.HORIZONTAL_PREPARED
        if concurrent_processes >= max(1, max_concurrent_integrations // 2):
            return ScalabilityMode.VERTICAL_PREPARED
        return ScalabilityMode.SINGLE_NODE

    def snapshot(self) -> dict[str, Any]:
        return {
            "readiness": self._readiness.to_dict(),
        }
