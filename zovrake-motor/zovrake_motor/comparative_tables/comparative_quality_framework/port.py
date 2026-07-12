"""Contrato base de auditores del Comparative Quality Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.comparative_quality_framework.enums import (
    ComparativeQualityValidatorStrategyType,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.gateway import (
    ComparativeQualityInputView,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidatorResult,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)


class ComparativeQualityValidatorPort(ABC):
    """Contrato común para auditores de calidad."""

    @property
    @abstractmethod
    def validator_name(self) -> str:
        """Identificador único del auditor."""

    @property
    @abstractmethod
    def validator_label(self) -> str:
        """Etiqueta descriptiva del auditor."""

    @property
    @abstractmethod
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        """Tipo de estrategia de auditoría."""

    @abstractmethod
    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        """Audita calidad — sin modificar datos evaluados."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "validator_label": self.validator_label,
            "validator_type": self.validator_type.value,
        }
