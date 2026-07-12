"""Modelos inmutables del OMMF — métricas, trazas y salud operativa."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.ommf.enums import (
    ComponentHealthStatus,
    PerformanceMetricKind,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class IntegrationTraceSpan:
    """
    Span de trazabilidad del flujo de integración.

    Conserva continuidad por process_id mediante trace_id compartido.
    """

    trace_id: str
    span_id: str
    process_id: UUID
    project_id: str
    quotation_id: str
    component: str
    pipeline_phase: str
    operation: str
    started_at: datetime
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        trace_id: str,
        process_id: UUID,
        project_id: str,
        quotation_id: str,
        component: str,
        pipeline_phase: str,
        operation: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> IntegrationTraceSpan:
        return cls(
            trace_id=trace_id,
            span_id=str(uuid4()),
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            component=component,
            pipeline_phase=pipeline_phase,
            operation=operation,
            started_at=utc_now(),
            duration_ms=duration_ms,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "process_id": str(self.process_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "component": self.component,
            "pipeline_phase": self.pipeline_phase,
            "operation": self.operation,
            "started_at": self.started_at.isoformat(),
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PerformanceMetricRecord:
    """Indicador de rendimiento registrado."""

    metric_id: str
    process_id: UUID
    kind: PerformanceMetricKind
    component: str
    duration_ms: float
    recorded_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        process_id: UUID,
        kind: PerformanceMetricKind,
        component: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> PerformanceMetricRecord:
        return cls(
            metric_id=str(uuid4()),
            process_id=process_id,
            kind=kind,
            component=component,
            duration_ms=duration_ms,
            recorded_at=utc_now(),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "process_id": str(self.process_id),
            "kind": self.kind.value,
            "component": self.component,
            "duration_ms": self.duration_ms,
            "recorded_at": self.recorded_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComponentHealthRecord:
    """Estado operativo de un componente."""

    component: str
    status: ComponentHealthStatus
    updated_at: datetime
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "updated_at": self.updated_at.isoformat(),
            "reason": self.reason,
            "metadata": self.metadata,
        }
