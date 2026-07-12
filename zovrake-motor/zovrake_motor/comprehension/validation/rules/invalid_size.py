"""Regla: tamaño inválido."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType, ValidationSeverity
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, passed_result

if TYPE_CHECKING:
    from zovrake_motor.config.categories.comprehension import DocumentValidationSettings


class InvalidSizeRule(ValidationRulePort):
    """Detecta tamaños inválidos según configuración central."""

    def __init__(self, *, settings: DocumentValidationSettings | None = None) -> None:
        self._settings = settings

    @property
    def rule_name(self) -> str:
        return "invalid_size_rule"

    @property
    def rule_label(self) -> str:
        return "Tamaño Inválido"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.INVALID_SIZE

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if request.file_size_bytes is None:
            return passed_result(self.rule_name)

        min_size = self._min_size()
        max_size = self._max_size()

        if request.file_size_bytes < min_size:
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message=f"Tamaño inferior al mínimo permitido ({min_size} bytes)",
            )

        if request.file_size_bytes > max_size:
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message=f"Tamaño superior al máximo permitido ({max_size} bytes)",
                severity=ValidationSeverity.ERROR,
            )

        return passed_result(self.rule_name)

    def _min_size(self) -> int:
        if self._settings is not None:
            return self._settings.min_file_size_bytes
        return 1

    def _max_size(self) -> int:
        if self._settings is not None:
            return self._settings.max_file_size_bytes
        return 50_000_000
