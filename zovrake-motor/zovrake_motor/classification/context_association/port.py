"""Contrato base de asociadores del Context Association Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.context_association.enums import ContextAssociatorStrategyType
from zovrake_motor.classification.context_association.gateway import ContextAssociationInputView
from zovrake_motor.classification.context_association.models import ContextAssociatorResult
from zovrake_motor.config.categories.classification import ContextAssociationSettings


class ContextAssociatorPort(ABC):
    """Contrato común para asociadores de contexto."""

    @property
    @abstractmethod
    def associator_name(self) -> str:
        """Identificador único del asociador."""

    @property
    @abstractmethod
    def associator_label(self) -> str:
        """Etiqueta descriptiva del asociador."""

    @property
    @abstractmethod
    def associator_type(self) -> ContextAssociatorStrategyType:
        """Tipo de estrategia de asociación."""

    @abstractmethod
    def associate(
        self,
        input_view: ContextAssociationInputView,
        *,
        settings: ContextAssociationSettings,
        start_sequence: int,
    ) -> ContextAssociatorResult:
        """Asocia contexto con grupos — sin modificar origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "associator_name": self.associator_name,
            "associator_label": self.associator_label,
            "associator_type": self.associator_type.value,
        }
