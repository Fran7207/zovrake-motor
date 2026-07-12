"""Coordinator de Cuadros Comparativos — orquestación estructural del módulo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.registry import ComponentRegistry


class ComparativeTablesCoordinator(ComparativeTablesComponentPort):
    """
    Coordinator de Generación de Cuadros Comparativos.

    Responsabilidad futura: orquestar el flujo interno de generación dinámica.
    En esta etapa administra únicamente la estructura de componentes.
    """

    def __init__(self, registry: ComponentRegistry) -> None:
        self._registry = registry

    @property
    def component_name(self) -> str:
        return "comparative_tables_coordinator"

    @property
    def component_label(self) -> str:
        return "Coordinator de Cuadros Comparativos"

    def is_ready(self) -> bool:
        return self._registry.count() > 0

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["components"] = self._registry.snapshot()
        base["components_count"] = self._registry.count()
        base["components_ready"] = self._registry.ready_count()
        return base
