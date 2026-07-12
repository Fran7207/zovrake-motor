"""Modelos inmutables del FTRRF."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.ftrrf.enums import (
    ErrorCategory,
    ErrorSeverity,
    RecoveryDecision,
    RecoveryStage,
    RecoveryStatus,
    RetryStrategy,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RetryPolicy:
    """Política centralizada de reintentos — configurable por categoría."""

    category: ErrorCategory
    recoverable: bool
    max_retries: int = 0
    interval_seconds: float = 0.0
    strategy: RetryStrategy = RetryStrategy.NONE
    cancel_on_categories: tuple[ErrorCategory, ...] = field(default_factory=tuple)

    def allows_retry(self, attempt: int) -> bool:
        return self.recoverable and attempt <= self.max_retries

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "recoverable": self.recoverable,
            "max_retries": self.max_retries,
            "interval_seconds": self.interval_seconds,
            "strategy": self.strategy.value,
            "cancel_on_categories": [item.value for item in self.cancel_on_categories],
        }


@dataclass(frozen=True)
class FaultClassification:
    """Resultado de la clasificación de un error."""

    category: ErrorCategory
    severity: ErrorSeverity
    recoverable: bool
    origin_component: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "origin_component": self.origin_component,
            "description": self.description,
        }


@dataclass(frozen=True)
class ErrorRecord:
    """Registro estructurado de un error — aislado por proceso."""

    error_id: str
    process_id: UUID
    category: ErrorCategory
    severity: ErrorSeverity
    description: str
    origin_component: str
    recovery_status: RecoveryStatus
    occurred_at: datetime = field(default_factory=utc_now)
    retry_count: int = 0
    recoverable: bool = False
    error_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        *,
        process_id: UUID,
        classification: FaultClassification,
        error_code: str = "",
        recovery_status: RecoveryStatus = RecoveryStatus.PENDING,
        retry_count: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ErrorRecord:
        return ErrorRecord(
            error_id=str(uuid4()),
            process_id=process_id,
            category=classification.category,
            severity=classification.severity,
            description=classification.description,
            origin_component=classification.origin_component,
            recovery_status=recovery_status,
            recoverable=classification.recoverable,
            error_code=error_code,
            retry_count=retry_count,
            metadata=dict(metadata or {}),
        )

    def with_status(
        self,
        recovery_status: RecoveryStatus,
        *,
        retry_count: int | None = None,
    ) -> ErrorRecord:
        return ErrorRecord(
            error_id=self.error_id,
            process_id=self.process_id,
            category=self.category,
            severity=self.severity,
            description=self.description,
            origin_component=self.origin_component,
            recovery_status=recovery_status,
            occurred_at=self.occurred_at,
            retry_count=retry_count if retry_count is not None else self.retry_count,
            recoverable=self.recoverable,
            error_code=self.error_code,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_id": self.error_id,
            "process_id": str(self.process_id),
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "origin_component": self.origin_component,
            "recovery_status": self.recovery_status.value,
            "occurred_at": self.occurred_at.isoformat(),
            "retry_count": self.retry_count,
            "recoverable": self.recoverable,
            "error_code": self.error_code,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class RecoveryOutcome:
    """Resultado de una acción de tolerancia a fallos."""

    process_id: UUID
    decision: RecoveryDecision
    stage: RecoveryStage
    error_record: ErrorRecord
    retry_policy: RetryPolicy
    retries_remaining: int
    message: str
    traceability_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def should_retry(self) -> bool:
        return self.decision == RecoveryDecision.RETRY

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "decision": self.decision.value,
            "stage": self.stage.value,
            "error_record": self.error_record.to_dict(),
            "retry_policy": self.retry_policy.to_dict(),
            "retries_remaining": self.retries_remaining,
            "message": self.message,
            "traceability_preserved": self.traceability_preserved,
            "metadata": self.metadata,
        }
