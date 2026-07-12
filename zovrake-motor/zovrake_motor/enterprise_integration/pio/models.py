"""Modelos del Pipeline Integration Orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.pio.enums import IntegrationPipelinePhase


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PipelineTransitionRecord:
    """Registro de una transición de fase del Pipeline."""

    from_phase: IntegrationPipelinePhase | None
    to_phase: IntegrationPipelinePhase
    occurred_at: datetime = field(default_factory=utc_now)
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_phase": self.from_phase.value if self.from_phase is not None else None,
            "to_phase": self.to_phase.value,
            "occurred_at": self.occurred_at.isoformat(),
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class PipelineExecutionContext:
    """
    Contexto de ejecución del Pipeline — trazabilidad completa.

    Mantiene identificadores y historial durante todo el ciclo.
    """

    process_id: UUID
    operation: str
    project_id: str = ""
    analysis_id: str = ""
    codigo_req: str = ""
    current_phase: IntegrationPipelinePhase | None = None
    transitions: list[PipelineTransitionRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    motor_invocation_prepared: bool = False
    motor_executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "operation": self.operation,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "codigo_req": self.codigo_req,
            "current_phase": self.current_phase.value if self.current_phase is not None else None,
            "transitions": [item.to_dict() for item in self.transitions],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "motor_invocation_prepared": self.motor_invocation_prepared,
            "motor_executed": self.motor_executed,
        }


@dataclass(frozen=True)
class PipelineOrchestrationResult:
    """Resultado estructural de una orquestación — sin lógica de negocio."""

    context: PipelineExecutionContext
    success: bool
    message: str
    phases_completed: tuple[IntegrationPipelinePhase, ...] = ()
    executed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "executed": self.executed,
            "phases_completed": [phase.value for phase in self.phases_completed],
            "context": self.context.to_dict(),
            "metadata": self.metadata,
        }
