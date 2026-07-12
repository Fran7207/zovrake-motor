"""Contrato base de validadores del Classification Quality Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.classification_quality.enums import QualityValidatorStrategyType
from zovrake_motor.classification.classification_quality.gateway import ComparativeDomainModelCatalogView
from zovrake_motor.classification.classification_quality.models import QualityValidatorResult
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings


class QualityValidatorPort(ABC):
    """Contrato común para validadores de calidad."""

    @property
    @abstractmethod
    def validator_name(self) -> str:
        """Identificador único del validador."""

    @property
    @abstractmethod
    def validator_label(self) -> str:
        """Etiqueta descriptiva del validador."""

    @property
    @abstractmethod
    def validator_type(self) -> QualityValidatorStrategyType:
        """Tipo de estrategia de validación."""

    @abstractmethod
    def validate(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> QualityValidatorResult:
        """Valida calidad — sin modificar datos evaluados."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "validator_label": self.validator_label,
            "validator_type": self.validator_type.value,
        }
