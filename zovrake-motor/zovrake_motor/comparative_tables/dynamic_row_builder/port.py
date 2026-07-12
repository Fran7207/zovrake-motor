"""Contrato base de constructores del Dynamic Row Builder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.dynamic_row_builder.enums import RowBuilderStrategyType
from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import RowBuildInputView
from zovrake_motor.comparative_tables.dynamic_row_builder.models import RowBuilderResult
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings


class DynamicRowBuilderPort(ABC):
    """Contrato común para constructores de filas dinámicas."""

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
    def builder_type(self) -> RowBuilderStrategyType:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        input_view: RowBuildInputView,
        *,
        settings: DynamicRowBuilderSettings,
        start_sequence: int,
    ) -> RowBuilderResult:
        """Construye filas — sin modificar catálogos de entrada."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type.value,
        }
