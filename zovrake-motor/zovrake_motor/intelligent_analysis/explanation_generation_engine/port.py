"""Contrato de generadores de explicaciones del EGE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ExplanationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import GeneratorResult
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings


class ExplanationGeneratorPort(ABC):
    """Contrato base para generadores de explicaciones."""

    @property
    @abstractmethod
    def generator_name(self) -> str:
        """Identificador único del generador."""

    @property
    @abstractmethod
    def generator_label(self) -> str:
        """Etiqueta descriptiva del generador."""

    @property
    @abstractmethod
    def generator_type(self) -> str:
        """Tipo de estrategia de generación."""

    @abstractmethod
    def generate(
        self,
        input_view: ExplanationGenerationInputView,
        *,
        settings: ExplanationGenerationEngineSettings,
        start_sequence: int,
    ) -> GeneratorResult:
        """Genera explicaciones sin modificar las entradas de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "generator_name": self.generator_name,
            "generator_label": self.generator_label,
            "generator_type": self.generator_type,
        }
