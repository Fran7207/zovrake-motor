"""Contrato base de estrategias de reconocimiento documental."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comprehension.recognition.enums import RecognitionStrategyType
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, StrategyRecognitionResult


class RecognitionStrategyPort(ABC):
    """
    Contrato común para todas las estrategias de reconocimiento.

    Cada estrategia tiene una única responsabilidad y es independiente.
    """

    @property
    @abstractmethod
    def strategy_type(self) -> RecognitionStrategyType:
        """Tipo de estrategia de reconocimiento."""

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Identificador único de la estrategia."""

    @property
    @abstractmethod
    def strategy_label(self) -> str:
        """Etiqueta descriptiva de la estrategia."""

    @abstractmethod
    def recognize(self, request: DocumentRecognitionRequest) -> StrategyRecognitionResult:
        """Identifica el formato — sin lectura de contenido en esta etapa."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "strategy_type": self.strategy_type.value,
            "strategy_name": self.strategy_name,
            "strategy_label": self.strategy_label,
        }
