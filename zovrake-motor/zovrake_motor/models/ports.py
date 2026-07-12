"""Contratos base compartidos del Motor Inteligente."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ModulePort(ABC):
    """
    Contrato base que todo módulo del Motor debe implementar.

    Definido en models para evitar dependencias entre módulos y el Coordinator.
    """

    @property
    @abstractmethod
    def module_name(self) -> str:
        """Identificador único del módulo."""

    @abstractmethod
    def is_available(self) -> bool:
        """Indica si el módulo está listo para ser coordinado."""

    @abstractmethod
    def initialize(self) -> None:
        """Inicializa el módulo — sin lógica de negocio en esta etapa."""
