"""Contrato base de constructores del Comparative Domain Model Builder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.comparative_domain_model.enums import DomainModelBuilderStrategyType
from zovrake_motor.classification.comparative_domain_model.gateway import ContextAssociationCatalogView
from zovrake_motor.classification.comparative_domain_model.models import DomainModelBuilderResult
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings


class ComparativeDomainModelBuilderPort(ABC):
    """Contrato común para constructores del modelo comparativo."""

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
    def builder_type(self) -> DomainModelBuilderStrategyType:
        """Tipo de estrategia de construcción."""

    @abstractmethod
    def build(
        self,
        catalog_view: ContextAssociationCatalogView,
        *,
        settings: ComparativeDomainModelBuilderSettings,
        start_sequence: int,
    ) -> DomainModelBuilderResult:
        """Construye modelos comparativos — sin modificar datos de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "builder_type": self.builder_type.value,
        }
