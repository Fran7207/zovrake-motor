"""Coordinator de Clasificación — orquestación estructural del módulo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.registry import ComponentRegistry


class ClassificationCoordinator(ClassificationComponentPort):
    """
    Coordinator de Clasificación.

    Responsabilidad futura: orquestar el flujo interno de clasificación inteligente.
    En esta etapa administra únicamente la estructura de componentes.
    """

    def __init__(self, registry: ComponentRegistry) -> None:
        self._registry = registry

    @property
    def component_name(self) -> str:
        return "classification_coordinator"

    @property
    def component_label(self) -> str:
        return "Coordinator de Clasificación"

    def is_ready(self) -> bool:
        return self._registry.count() > 0

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["components"] = self._registry.snapshot()
        base["components_count"] = self._registry.count()
        base["components_ready"] = self._registry.ready_count()
        return base
