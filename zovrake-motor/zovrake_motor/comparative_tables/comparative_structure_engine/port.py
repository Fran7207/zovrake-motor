"""Contrato base de constructores del Comparative Structure Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.comparative_structure_engine.enums import (
    StructureBuilderStrategyType,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.gateway import (
    DomainModelCatalogView,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import StructureBuilderResult
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings


class ComparativeStructureBuilderPort(ABC):
    """Contrato común para constructores de estructuras comparativas."""

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
    def builder_type(self) -> StructureBuilderStrategyType:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        catalog_view: DomainModelCatalogView,
        *,
        settings: ComparativeStructureEngineSettings,
        start_sequence: int,
    ) -> StructureBuilderResult:
        """Construye estructuras — sin modificar el Modelo Comparativo de Dominio."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type.value,
        }
