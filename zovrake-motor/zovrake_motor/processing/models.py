"""Modelos del Pipeline Interno del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.processing.enums import PipelineExecutionState, PipelineStageType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StageRecord:
    """Registro estructural de una etapa recorrida."""

    stage: PipelineStageType
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "message": self.message,
        }


@dataclass
class StageTransition:
    """Transición secuencial entre etapas."""

    from_stage: PipelineStageType | None
    to_stage: PipelineStageType
    occurred_at: datetime = field(default_factory=_utc_now)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_stage": self.from_stage.value if self.from_stage else None,
            "to_stage": self.to_stage.value,
            "occurred_at": self.occurred_at.isoformat(),
            "reason": self.reason,
        }


@dataclass
class PipelineContext:
    """
    Contexto compartido que acompaña una solicitud durante su recorrido.

    Estructura preparada para compartir información entre módulos futuros
    sin comunicación directa entre ellos.
    """

    process_id: UUID
    current_stage: PipelineStageType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    stage_records: list[StageRecord] = field(default_factory=list)
    transitions: list[StageTransition] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "current_stage": self.current_stage.value if self.current_stage else None,
            "metadata": self.metadata,
            "stage_records": [record.to_dict() for record in self.stage_records],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PipelineExecution:
    """Ejecución estructural de un recorrido por el Pipeline."""

    context: PipelineContext
    state: PipelineExecutionState = PipelineExecutionState.PENDIENTE
    stop_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "stop_reason": self.stop_reason,
            "context": self.context.to_dict(),
        }


@dataclass
class PipelineResult:
    """Resultado del recorrido secuencial — sin datos de negocio."""

    process_id: UUID
    success: bool
    state: PipelineExecutionState
    message: str
    stages_completed: list[PipelineStageType] = field(default_factory=list)
    context: PipelineContext | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "success": self.success,
            "state": self.state.value,
            "message": self.message,
            "stages_completed": [stage.value for stage in self.stages_completed],
            "context": self.context.to_dict() if self.context else None,
        }
