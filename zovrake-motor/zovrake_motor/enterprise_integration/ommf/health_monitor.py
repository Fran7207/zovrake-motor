"""Monitor de salud operativa de componentes — sin comprobaciones automáticas."""

from __future__ import annotations

from typing import Any

from zovrake_motor.enterprise_integration.ommf.enums import ComponentHealthStatus
from zovrake_motor.enterprise_integration.ommf.models import ComponentHealthRecord, utc_now


class HealthMonitor:
    """Representa el estado operativo de cada componente."""

    def __init__(self) -> None:
        self._health: dict[str, ComponentHealthRecord] = {}

    def update(
        self,
        component: str,
        status: ComponentHealthStatus,
        *,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ComponentHealthRecord:
        record = ComponentHealthRecord(
            component=component,
            status=status,
            updated_at=utc_now(),
            reason=reason,
            metadata=dict(metadata or {}),
        )
        self._health[component] = record
        return record

    def get(self, component: str) -> ComponentHealthStatus:
        record = self._health.get(component)
        if record is None:
            return ComponentHealthStatus.AVAILABLE
        return record.status

    def snapshot(self) -> dict[str, Any]:
        return {
            component: record.to_dict()
            for component, record in self._health.items()
        }
