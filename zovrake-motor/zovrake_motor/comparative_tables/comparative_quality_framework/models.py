"""Modelos del Comparative Quality Framework e informe de auditoría."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_quality_framework.enums import (
    ComparativeQualityCategory,
    ComparativeQualityValidationStatus,
)


@dataclass(frozen=True)
class ComparativeQualityFinding:
    """Hallazgo individual de una auditoría."""

    validator_name: str
    category: ComparativeQualityCategory
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
class ComparativeQualityCheck:
    """Resultado de una verificación individual."""

    validator_name: str
    category: ComparativeQualityCategory
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
class ComparativeQualityReport:
    """
    Informe interno de auditoría — preparado para certificación (4.11).

    No modifica los datos evaluados.
    """

    report_id: str
    process_id: UUID
    catalog_id: str
    document_id: str
    model_id: str
    validation_report_id: str
    findings: tuple[ComparativeQualityFinding, ...]
    checks: tuple[ComparativeQualityCheck, ...]
    checks_executed: int
    checks_passed: int
    checks_failed: int
    overall_status: ComparativeQualityValidationStatus
    module_certification_prepared: bool = True
    definitive_catalog_preserved: bool = True
    validation_report_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "process_id": str(self.process_id),
            "catalog_id": self.catalog_id,
            "document_id": self.document_id,
            "model_id": self.model_id,
            "validation_report_id": self.validation_report_id,
            "findings": [finding.to_dict() for finding in self.findings],
            "checks": [check.to_dict() for check in self.checks],
            "checks_executed": self.checks_executed,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "overall_status": self.overall_status.value,
            "module_certification_prepared": self.module_certification_prepared,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "validation_report_preserved": self.validation_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeQualityValidatorResult:
    """Resultado individual de un auditor."""

    validator_type: str
    validator_name: str
    checks: tuple[ComparativeQualityCheck, ...] = ()
    findings: tuple[ComparativeQualityFinding, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeQualityValidationRequest:
    """
    Solicitud de auditoría de calidad.

    El CQF consume exclusivamente el catálogo del CMB y el reporte del CVF.
    """

    process_id: UUID
    definitive_catalog: dict[str, Any]
    validation_report: dict[str, Any]
    pipeline_snapshot: list[dict[str, Any]] | None = None
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeQualityValidationResult:
    """Resultado uniforme de la auditoría de calidad."""

    process_id: UUID
    document_id: str
    model_id: str
    report: ComparativeQualityReport
    status: ComparativeQualityValidationStatus
    definitive_catalog_preserved: bool
    validation_report_preserved: bool
    domain_model_preserved: bool
    validators_executed: int
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "report": self.report.to_dict(),
            "status": self.status.value,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "validation_report_preserved": self.validation_report_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "validators_executed": self.validators_executed,
            "technical_observations": list(self.technical_observations),
        }
