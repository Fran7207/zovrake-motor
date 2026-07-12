"""Coordinator de Razonamiento Inteligente — orquestación estructural del módulo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.registry import ComponentRegistry


class IntelligentAnalysisCoordinator(IntelligentAnalysisComponentPort):
    """
    Coordinator de Razonamiento y Resultado del Análisis Inteligente.

    Responsabilidad futura: orquestar el flujo interno de razonamiento basado en evidencias.
    En esta etapa administra únicamente la estructura de componentes.
    """

    def __init__(self, registry: ComponentRegistry) -> None:
        self._registry = registry
        self._initialized = False

    @property
    def component_name(self) -> str:
        return "intelligent_analysis_coordinator"

    @property
    def component_label(self) -> str:
        return "Coordinator de Razonamiento Inteligente"

    def initialize(self) -> None:
        self._initialized = True

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() > 0

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["components"] = self._registry.snapshot()
        base["components_count"] = self._registry.count()
        base["components_ready"] = self._registry.ready_count()
        return base
