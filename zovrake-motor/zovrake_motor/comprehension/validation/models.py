"""Modelos del Document Validation Framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.validation.enums import (
    DocumentQualityLevel,
    ValidationIncidentType,
    ValidationSeverity,
    ValidationStatus,
)


@dataclass(frozen=True)
class ValidationIncident:
    """Incidencia detectada durante la validación."""

    incident_type: ValidationIncidentType
    rule_name: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_type": self.incident_type.value,
            "rule_name": self.rule_name,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class ValidationWarning:
    """Advertencia detectada durante la validación."""

    rule_name: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.WARNING

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class DocumentValidationRequest:
    """Solicitud de validación documental — sin lectura de archivos."""

    process_id: UUID
    document_id: str
    file_name: str = ""
    format_type: str | None = None
    file_size_bytes: int | None = None
    accessible: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationRuleResult:
    """Resultado individual de una regla de validación."""

    rule_name: str
    passed: bool
    incidents: tuple[ValidationIncident, ...] = ()
    warnings: tuple[ValidationWarning, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "passed": self.passed,
            "incidents": [item.to_dict() for item in self.incidents],
            "warnings": [item.to_dict() for item in self.warnings],
            "technical_observations": list(self.technical_observations),
        }


@dataclass(frozen=True)
class DocumentValidationResult:
    """Resultado estructurado y uniforme de validación documental."""

    process_id: UUID
    document_id: str
    status: ValidationStatus
    incidents: tuple[ValidationIncident, ...]
    warnings: tuple[ValidationWarning, ...]
    quality_level: DocumentQualityLevel
    technical_observations: tuple[str, ...]
    rules_executed: int = 0
    rules_passed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "status": self.status.value,
            "incidents": [item.to_dict() for item in self.incidents],
            "warnings": [item.to_dict() for item in self.warnings],
            "quality_level": self.quality_level.value,
            "technical_observations": list(self.technical_observations),
            "rules_executed": self.rules_executed,
            "rules_passed": self.rules_passed,
        }
