"""Contrato base de constructores del Dynamic Column Builder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.dynamic_column_builder.enums import ColumnBuilderStrategyType
from zovrake_motor.comparative_tables.dynamic_column_builder.gateway import StructureCatalogView
from zovrake_motor.comparative_tables.dynamic_column_builder.models import ColumnBuilderResult
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


class DynamicColumnBuilderPort(ABC):
    """Contrato común para constructores de columnas dinámicas."""

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
    def builder_type(self) -> ColumnBuilderStrategyType:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        catalog_view: StructureCatalogView,
        *,
        settings: DynamicColumnBuilderSettings,
        start_sequence: int,
    ) -> ColumnBuilderResult:
        """Construye columnas — sin modificar el catálogo de estructuras."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type.value,
        }
