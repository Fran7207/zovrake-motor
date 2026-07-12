"""Modelos del Classification Quality Framework e informe de validación."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.classification_quality.enums import (
    QualityValidationCategory,
    QualityValidationStatus,
)


@dataclass(frozen=True)
class QualityValidationFinding:
    """Hallazgo individual de una validación."""

    validator_name: str
    category: QualityValidationCategory
    message: str
    severity: str = "info"
    target_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "category": self.category.value,
            "message": self.message,
            "severity": self.severity,
            "target_id": self.target_id,
        }


@dataclass(frozen=True)
class QualityValidationCheck:
    """Resultado de una verificación individual."""

    validator_name: str
    category: QualityValidationCategory
    check_name: str
    passed: bool
    message: str
    target_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_name": self.validator_name,
            "category": self.category.value,
            "check_name": self.check_name,
            "passed": self.passed,
            "message": self.message,
            "target_id": self.target_id,
        }


@dataclass(frozen=True)
class ClassificationQualityReport:
    """
    Informe interno de validación — preparado para certificación (3.11).

    No modifica los datos evaluados.
    """

    report_id: str
    process_id: UUID
    catalog_id: str
    document_id: str
    model_id: str
    findings: tuple[QualityValidationFinding, ...]
    checks: tuple[QualityValidationCheck, ...]
    checks_executed: int
    checks_passed: int
    checks_failed: int
    overall_status: QualityValidationStatus
    certification_prepared: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "process_id": str(self.process_id),
            "catalog_id": self.catalog_id,
            "document_id": self.document_id,
            "model_id": self.model_id,
            "findings": [finding.to_dict() for finding in self.findings],
            "checks": [check.to_dict() for check in self.checks],
            "checks_executed": self.checks_executed,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "overall_status": self.overall_status.value,
            "certification_prepared": self.certification_prepared,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class QualityValidatorResult:
    """Resultado individual de un validador."""

    validator_type: str
    validator_name: str
    checks: tuple[QualityValidationCheck, ...] = ()
    findings: tuple[QualityValidationFinding, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClassificationQualityValidationRequest:
    """
    Solicitud de validación de calidad.

    El CQF consume exclusivamente el catálogo del CDMB.
    """

    process_id: UUID
    comparative_domain_model_catalog: dict[str, Any]
    pipeline_snapshot: list[dict[str, Any]] | None = None
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClassificationQualityValidationResult:
    """Resultado uniforme de la validación de calidad."""

    process_id: UUID
    document_id: str
    model_id: str
    report: ClassificationQualityReport
    status: QualityValidationStatus
    source_data_preserved: bool
    validators_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "report": self.report.to_dict(),
            "status": self.status.value,
            "source_data_preserved": self.source_data_preserved,
            "validators_executed": self.validators_executed,
            "technical_observations": list(self.technical_observations),
        }
