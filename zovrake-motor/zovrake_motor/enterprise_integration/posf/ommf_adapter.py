"""Adaptador de consumo de métricas OMMF — evaluación de rendimiento."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.ommf.framework import (
        ObservabilityMetricsMonitoringFramework,
    )


class EnterpriseIntegrationPosfOmmfAdapter:
    """Provee métricas del OMMF al POSF sin acoplamiento circular."""

    def __init__(self, ommf: ObservabilityMetricsMonitoringFramework) -> None:
        self._ommf = ommf

    def observability_snapshot(self) -> dict[str, Any]:
        return self._ommf.observability_snapshot()

    def traces_for_process(self, process_id: UUID) -> tuple[dict[str, Any], ...]:
        return self._ommf.traces_for_process(process_id)
