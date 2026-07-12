"""Contrato base de validadores del Group Integrity Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.group_integrity_engine.enums import (
    IntegrityValidatorStrategyType,
)
from zovrake_motor.comparative_tables.group_integrity_engine.gateway import (
    IntegrityValidationInputView,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import IntegrityValidatorResult
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings


class IntegrityValidatorPort(ABC):
    """Contrato común para validadores de integridad estructural."""

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
    def validator_type(self) -> IntegrityValidatorStrategyType:
        """Tipo de estrategia de validación."""

    @abstractmethod
    def validate(
        self,
        input_view: IntegrityValidationInputView,
        *,
        settings: GroupIntegrityEngineSettings,
        start_sequence: int,
    ) -> IntegrityValidatorResult:
        """Valida integridad — sin modificar catálogos de entrada."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "validator_label": self.validator_label,
            "validator_type": self.validator_type.value,
        }
