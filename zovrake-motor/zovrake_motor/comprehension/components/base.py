"""Contratos base de componentes internos de Comprensión Documental."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ComprehensionComponentPort(ABC):
    """
    Contrato base para componentes del módulo de Comprensión Documental.

    Cada componente tiene una única responsabilidad definida.
    """

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Identificador único del componente."""

    @property
    @abstractmethod
    def component_label(self) -> str:
        """Etiqueta descriptiva del componente."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Indica si el componente está preparado para etapas futuras."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "component_label": self.component_label,
            "ready": self.is_ready(),
        }
