"""Contrato base de validadores del Comparative Validation Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ValidationValidatorStrategyType,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.gateway import (
    ModelValidationInputView,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ValidationValidatorResult,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)


class ValidationValidatorPort(ABC):
    """Contrato común para validadores del Modelo Comparativo Definitivo."""

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
    def validator_type(self) -> ValidationValidatorStrategyType:
        """Tipo de estrategia de validación."""

    @abstractmethod
    def validate(
        self,
        input_view: ModelValidationInputView,
        *,
        settings: ComparativeValidationFrameworkSettings,
        start_sequence: int,
    ) -> ValidationValidatorResult:
        """Valida modelos definitivos — sin modificar catálogos de entrada."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "validator_label": self.validator_label,
            "validator_type": self.validator_type.value,
        }
