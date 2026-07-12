"""Optimizador lógico de recursos — sin dependencia del sistema operativo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.enterprise_integration.posf.enums import ResourceKind
from zovrake_motor.enterprise_integration.posf.models import ResourceUsageSnapshot, utc_now


class ResourceOptimizer:
    """
    Rastrea uso lógico de memoria, CPU, almacenamiento temporal y recursos compartidos.

    No implementa optimizaciones dependientes del SO.
    """

    def __init__(self) -> None:
        self._usage: dict[str, int] = {kind.value: 0 for kind in ResourceKind}
        self._snapshots: list[ResourceUsageSnapshot] = []

    def record(self, *, kind: ResourceKind, units: int, component: str) -> None:
        self._usage[kind.value] = max(0, self._usage[kind.value] + units)
        self._snapshots.append(
            ResourceUsageSnapshot(
                kind=kind,
                units=units,
                component=component,
                recorded_at=utc_now(),
            ),
        )

    def release(self, *, kind: ResourceKind, units: int, component: str) -> None:
        self._usage[kind.value] = max(0, self._usage[kind.value] - units)
        self._snapshots.append(
            ResourceUsageSnapshot(
                kind=kind,
                units=-units,
                component=component,
                recorded_at=utc_now(),
            ),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "current_usage": dict(self._usage),
            "total_records": len(self._snapshots),
            "recent": [item.to_dict() for item in self._snapshots[-10:]],
        }
