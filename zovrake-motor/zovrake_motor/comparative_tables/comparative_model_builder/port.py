"""Contrato base de constructores del Comparative Model Builder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.comparative_model_builder.enums import (
    ModelBuilderStrategyType,
)
from zovrake_motor.comparative_tables.comparative_model_builder.gateway import ModelBuildInputView
from zovrake_motor.comparative_tables.comparative_model_builder.models import ModelBuilderResult
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings


class ModelBuilderPort(ABC):
    """Contrato común para constructores del Modelo Comparativo Definitivo."""

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
    def builder_type(self) -> ModelBuilderStrategyType:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        input_view: ModelBuildInputView,
        *,
        settings: ComparativeModelBuilderSettings,
        start_sequence: int,
    ) -> ModelBuilderResult:
        """Construye modelos definitivos — sin modificar catálogos de entrada."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type.value,
        }
