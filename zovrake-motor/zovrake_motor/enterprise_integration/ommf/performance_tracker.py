"""Registro de indicadores de rendimiento — sin optimización."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ommf.enums import PerformanceMetricKind
from zovrake_motor.enterprise_integration.ommf.models import PerformanceMetricRecord


class PerformanceTracker:
    """Registra tiempos de operación sin alterar el flujo."""

    def __init__(self) -> None:
        self._records: list[PerformanceMetricRecord] = []
        self._totals: dict[str, float] = {}
        self._counts: dict[str, int] = {}

    def record(
        self,
        *,
        process_id: UUID,
        kind: PerformanceMetricKind,
        component: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> PerformanceMetricRecord:
        record = PerformanceMetricRecord.create(
            process_id=process_id,
            kind=kind,
            component=component,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        self._records.append(record)
        key = kind.value
        self._totals[key] = self._totals.get(key, 0.0) + duration_ms
        self._counts[key] = self._counts.get(key, 0) + 1
        return record

    def average(self, kind: PerformanceMetricKind) -> float:
        key = kind.value
        count = self._counts.get(key, 0)
        if count == 0:
            return 0.0
        return self._totals[key] / count

    def count(self) -> int:
        return len(self._records)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total_records": self.count(),
            "averages_ms": {
                kind.value: self.average(kind)
                for kind in PerformanceMetricKind
            },
            "recent": [record.to_dict() for record in self._records[-20:]],
        }
