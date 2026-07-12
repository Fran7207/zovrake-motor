"""Utilidades compartidas para reglas de validación."""

from __future__ import annotations

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType, ValidationSeverity
from zovrake_motor.comprehension.validation.models import (
    DocumentValidationRequest,
    ValidationIncident,
    ValidationRuleResult,
    ValidationWarning,
)


def metadata_flag(request: DocumentValidationRequest, key: str) -> bool:
    return bool(request.metadata.get(key, False))


def passed_result(
    rule_name: str,
    *,
    observation: str = "Regla preparada — sin evaluación de archivo en esta etapa",
) -> ValidationRuleResult:
    return ValidationRuleResult(
        rule_name=rule_name,
        passed=True,
        technical_observations=(observation,),
    )


def failed_result(
    rule_name: str,
    *,
    incident_type: ValidationIncidentType,
    message: str,
    severity: ValidationSeverity = ValidationSeverity.ERROR,
) -> ValidationRuleResult:
    return ValidationRuleResult(
        rule_name=rule_name,
        passed=False,
        incidents=(
            ValidationIncident(
                incident_type=incident_type,
                rule_name=rule_name,
                message=message,
                severity=severity,
            ),
        ),
    )


def warning_result(
    rule_name: str,
    *,
    message: str,
) -> ValidationRuleResult:
    return ValidationRuleResult(
        rule_name=rule_name,
        passed=True,
        warnings=(
            ValidationWarning(
                rule_name=rule_name,
                message=message,
            ),
        ),
        technical_observations=("Advertencia registrada — sin bloqueo en esta etapa",),
    )
