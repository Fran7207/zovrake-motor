"""Regla: formato no soportado."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, passed_result

if TYPE_CHECKING:
    from zovrake_motor.config.categories.comprehension import DocumentValidationSettings


class UnsupportedFormatRule(ValidationRulePort):
    """Detecta formatos no soportados según configuración central."""

    def __init__(self, *, settings: DocumentValidationSettings | None = None) -> None:
        self._settings = settings

    @property
    def rule_name(self) -> str:
        return "unsupported_format_rule"

    @property
    def rule_label(self) -> str:
        return "Formato No Soportado"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.UNSUPPORTED_FORMAT

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if request.format_type is None:
            return passed_result(self.rule_name)

        supported = self._supported_formats()
        if supported and request.format_type.lower() not in supported:
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message=f"Formato no soportado: {request.format_type}",
            )
        return passed_result(self.rule_name)

    def _supported_formats(self) -> tuple[str, ...]:
        if self._settings is not None:
            return self._settings.supported_formats
        return ("pdf", "docx", "xlsx", "image")
