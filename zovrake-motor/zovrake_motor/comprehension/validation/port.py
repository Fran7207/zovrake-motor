"""Contrato base de reglas de validación documental."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult


class ValidationRulePort(ABC):
    """
    Contrato común para todas las reglas de validación documental.

    Cada regla tiene una única responsabilidad y es independiente.
    """

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Identificador único de la regla."""

    @property
    @abstractmethod
    def rule_label(self) -> str:
        """Etiqueta descriptiva de la regla."""

    @property
    @abstractmethod
    def incident_type(self) -> ValidationIncidentType:
        """Tipo de incidencia que detecta esta regla."""

    @abstractmethod
    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        """Evalúa la solicitud — sin lectura de archivos en esta etapa."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "rule_label": self.rule_label,
            "incident_type": self.incident_type.value,
        }
