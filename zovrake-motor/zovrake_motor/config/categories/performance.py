"""Configuración de rendimiento del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceSettings:
    """Rendimiento y monitoreo — estructura preparada para métricas futuras."""

    monitoring_enabled: bool = False
    metrics_collection_enabled: bool = False

    @classmethod
    def default(cls) -> PerformanceSettings:
        return cls()
