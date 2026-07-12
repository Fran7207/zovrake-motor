"""Modelos del Comparative Validation Framework — validación no destructiva."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ComparativeModelValidationStatus,
    ValidationFindingCategory,
    ValidationFindingSeverity,
)


@dataclass(frozen=True)
class ComparativeValidationTraceability:
    """Trazabilidad del reporte de validación."""

    process_id: UUID
    document_id: str
    model_id: str
    source_definitive_catalog_id: str
    definitive_catalog_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ComparativeValidationFinding:
    """Hallazgo de validación — sin modificación de datos."""

    finding_id: str
    category: ValidationFindingCategory
    severity: ValidationFindingSeverity
    definitive_model_id: str
    group_id: str
    message: str
    validator_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "message": self.message,
            "validator_name": self.validator_name,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeValidationCheckSet:
    """Conjunto de validaciones para un Modelo Comparativo Definitivo."""

    definitive_model_id: str
    group_id: str
    comparative_table_id: str
    findings: tuple[ComparativeValidationFinding, ...]
    is_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "findings": [finding.to_dict() for finding in self.findings],
            "findings_count": len(self.findings),
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True)
class ComparativeValidationReport:
    """Reporte de validación del Modelo Comparativo Definitivo."""

    report_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_definitive_catalog_id: str
    check_sets: tuple[ComparativeValidationCheckSet, ...]
    global_findings: tuple[ComparativeValidationFinding, ...]
    traceability: ComparativeValidationTraceability
    comparative_quality_framework_prepared: bool = True
    definitive_catalog_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "check_sets": [check_set.to_dict() for check_set in self.check_sets],
            "check_sets_count": len(self.check_sets),
            "global_findings": [finding.to_dict() for finding in self.global_findings],
            "global_findings_count": len(self.global_findings),
            "traceability": self.traceability.to_dict(),
            "comparative_quality_framework_prepared": self.comparative_quality_framework_prepared,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class ValidationValidatorResult:
    """Resultado individual de un validador."""

    validator_type: str
    validator_name: str
    check_sets: tuple[ComparativeValidationCheckSet, ...] = ()
    global_findings: tuple[ComparativeValidationFinding, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparativeModelValidationRequest:
    """
    Solicitud de validación del Modelo Comparativo Definitivo.

    El CVF consume exclusivamente el catálogo generado por el CMB.
    """

    process_id: UUID
    definitive_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparativeModelValidationResult:
    """Resultado uniforme de la validación del modelo comparativo definitivo."""

    process_id: UUID
    document_id: str
    model_id: str
    report: ComparativeValidationReport
    status: ComparativeModelValidationStatus
    findings_count: int
    error_count: int
    warning_count: int
    definitive_catalog_preserved: bool
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
            "findings_count": self.findings_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "validators_executed": self.validators_executed,
            "technical_observations": list(self.technical_observations),
        }
