"""Modelos inmutables del SVAF."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.svaf.enums import (
    AuditOperationResult,
    IntegrityIssueType,
    ValidationDirection,
    ValidationStage,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ValidationIssue:
    """Incidencia de validación estructural."""

    field: str
    message: str
    issue_type: IntegrityIssueType = IntegrityIssueType.INVALID_STRUCTURE

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "issue_type": self.issue_type.value,
        }


@dataclass(frozen=True)
class ValidationResult:
    """Resultado del motor de validación — sin validación de negocio."""

    approved: bool
    stage: ValidationStage
    direction: ValidationDirection
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "stage": self.stage.value,
            "direction": self.direction.value,
            "issues": [issue.to_dict() for issue in self.issues],
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class AuditRecord:
    """Registro de auditoría — trazabilidad completa de operaciones."""

    audit_id: str
    process_id: UUID
    operation: str
    component: str
    direction: ValidationDirection
    result: AuditOperationResult
    process_state: str = ""
    occurred_at: datetime = field(default_factory=utc_now)
    errors_detected: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        *,
        process_id: UUID,
        operation: str,
        component: str,
        direction: ValidationDirection,
        result: AuditOperationResult,
        process_state: str = "",
        errors_detected: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        return AuditRecord(
            audit_id=str(uuid4()),
            process_id=process_id,
            operation=operation,
            component=component,
            direction=direction,
            result=result,
            process_state=process_state,
            errors_detected=errors_detected,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "process_id": str(self.process_id),
            "operation": self.operation,
            "component": self.component,
            "direction": self.direction.value,
            "result": self.result.value,
            "process_state": self.process_state,
            "occurred_at": self.occurred_at.isoformat(),
            "errors_detected": list(self.errors_detected),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SecurityValidationOutcome:
    """Resultado consolidado de validación, integridad y auditoría."""

    approved: bool
    validation: ValidationResult
    audit_record: AuditRecord | None = None
    notified_ftrrf: bool = False
    pipeline_blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "validation": self.validation.to_dict(),
            "audit_record": self.audit_record.to_dict() if self.audit_record else None,
            "notified_ftrrf": self.notified_ftrrf,
            "pipeline_blocked": self.pipeline_blocked,
        }
