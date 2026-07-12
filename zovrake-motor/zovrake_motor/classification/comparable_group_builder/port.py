"""Contrato base de constructores del Comparable Group Builder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.comparable_group_builder.enums import GroupBuilderStrategyType
from zovrake_motor.classification.comparable_group_builder.gateway import EquivalenceCatalogView
from zovrake_motor.classification.comparable_group_builder.models import GroupBuilderResult
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings


class ComparableGroupBuilderPort(ABC):
    """Contrato común para constructores de grupos comparables."""

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
    def builder_type(self) -> GroupBuilderStrategyType:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        catalog_view: EquivalenceCatalogView,
        *,
        settings: ComparableGroupBuilderSettings,
        start_sequence: int,
    ) -> GroupBuilderResult:
        """Construye grupos — sin modificar el catálogo de equivalencias."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type.value,
        }
