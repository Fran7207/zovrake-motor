"""Recopilador de métricas operativas — sin estadísticas avanzadas."""

from __future__ import annotations

from typing import Any


class MetricsCollector:
    """
    Recopila contadores operativos del flujo de integración.

    Único punto autorizado para métricas agregadas del módulo.
    """

    def __init__(self) -> None:
        self._counters: dict[str, int] = {
            "requests_received": 0,
            "requests_processed": 0,
            "processes_successful": 0,
            "processes_failed": 0,
            "processes_cancelled": 0,
            "processes_recovered": 0,
            "retries_executed": 0,
            "validations_performed": 0,
            "audits_recorded": 0,
        }

    def increment(self, metric: str, amount: int = 1) -> None:
        if metric not in self._counters:
            self._counters[metric] = 0
        self._counters[metric] += amount

    def snapshot(self) -> dict[str, Any]:
        return dict(self._counters)
