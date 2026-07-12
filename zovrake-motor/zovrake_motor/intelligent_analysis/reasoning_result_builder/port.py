"""Contrato de constructores del RRB."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.intelligent_analysis.reasoning_result_builder.gateway import ReasoningResultInputView
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import BuilderResult
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings


class ReasoningResultBuilderPort(ABC):
    """Contrato base para constructores de resultados."""

    @property
    @abstractmethod
    def builder_name(self) -> str:
        """Identificador único del constructor."""

    @property
    @abstractmethod
    def builder_label(self) -> str:
        """Etiqueta descriptiva del constructor."""

    @property
    @abstractmethod
    def builder_type(self) -> str:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        input_view: ReasoningResultInputView,
        *,
        settings: ReasoningResultBuilderSettings,
        start_sequence: int,
    ) -> BuilderResult:
        """Construye resultados sin modificar las entradas de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type,
        }
