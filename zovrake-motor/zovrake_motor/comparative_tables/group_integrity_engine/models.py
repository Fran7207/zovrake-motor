"""Modelos del Group Integrity Engine — validación no destructiva."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.group_integrity_engine.enums import (
    GroupIntegrityValidationStatus,
    IntegrityFindingCategory,
    IntegrityFindingSeverity,
)


@dataclass(frozen=True)
class GroupIntegrityTraceability:
    """Trazabilidad del reporte de integridad."""

    process_id: UUID
    document_id: str
    model_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_provider_catalog_id: str
    structure_catalog_preserved: bool
    column_catalog_preserved: bool
    row_catalog_preserved: bool
    provider_catalog_preserved: bool
    domain_model_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "source_provider_catalog_id": self.source_provider_catalog_id,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class GroupIntegrityFinding:
    """Hallazgo de integridad — sin modificación de datos."""

    finding_id: str
    category: IntegrityFindingCategory
    severity: IntegrityFindingSeverity
    group_id: str
    table_id: str
    message: str
    validator_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "group_id": self.group_id,
            "table_id": self.table_id,
            "message": self.message,
            "validator_name": self.validator_name,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GroupIntegrityCheckSet:
    """Conjunto de validaciones para un Grupo Comparable."""

    table_id: str
    group_id: str
    findings: tuple[GroupIntegrityFinding, ...]
    is_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "group_id": self.group_id,
            "findings": [finding.to_dict() for finding in self.findings],
            "findings_count": len(self.findings),
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True)
class GroupIntegrityReport:
    """Reporte de integridad estructural del proceso."""

    report_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_provider_catalog_id: str
    check_sets: tuple[GroupIntegrityCheckSet, ...]
    global_findings: tuple[GroupIntegrityFinding, ...]
    traceability: GroupIntegrityTraceability
    traceability_metadata_engine_prepared: bool = True
    structure_catalog_preserved: bool = True
    column_catalog_preserved: bool = True
    row_catalog_preserved: bool = True
    provider_catalog_preserved: bool = True
    domain_model_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_structure_catalog_id": self.source_structure_catalog_id,
            "source_column_catalog_id": self.source_column_catalog_id,
            "source_row_catalog_id": self.source_row_catalog_id,
            "source_provider_catalog_id": self.source_provider_catalog_id,
            "check_sets": [check_set.to_dict() for check_set in self.check_sets],
            "check_sets_count": len(self.check_sets),
            "global_findings": [finding.to_dict() for finding in self.global_findings],
            "global_findings_count": len(self.global_findings),
            "traceability": self.traceability.to_dict(),
            "traceability_metadata_engine_prepared": self.traceability_metadata_engine_prepared,
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
        }


@dataclass(frozen=True)
class IntegrityValidatorResult:
    """Resultado individual de un validador de integridad."""

    validator_type: str
    validator_name: str
    check_sets: tuple[GroupIntegrityCheckSet, ...] = ()
    global_findings: tuple[GroupIntegrityFinding, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroupIntegrityValidationRequest:
    """
    Solicitud de validación de integridad estructural.

    El GIE consume exclusivamente los catálogos del CSE, DCB, DRB y POE.
    """

    process_id: UUID
    structure_catalog: dict[str, Any]
    column_catalog: dict[str, Any]
    row_catalog: dict[str, Any]
    provider_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GroupIntegrityValidationResult:
    """Resultado uniforme de la validación de integridad."""

    process_id: UUID
    document_id: str
    model_id: str
    report: GroupIntegrityReport
    status: GroupIntegrityValidationStatus
    findings_count: int
    error_count: int
    warning_count: int
    structure_catalog_preserved: bool
    column_catalog_preserved: bool
    row_catalog_preserved: bool
    provider_catalog_preserved: bool
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
            "structure_catalog_preserved": self.structure_catalog_preserved,
            "column_catalog_preserved": self.column_catalog_preserved,
            "row_catalog_preserved": self.row_catalog_preserved,
            "provider_catalog_preserved": self.provider_catalog_preserved,
            "domain_model_preserved": self.domain_model_preserved,
            "validators_executed": self.validators_executed,
            "technical_observations": list(self.technical_observations),
        }
