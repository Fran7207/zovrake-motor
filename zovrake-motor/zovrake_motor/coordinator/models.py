"""Modelos internos del Coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.coordinator.enums import CoordinationPhase, CoordinatorState


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PhaseRecord:
    """Registro de una fase del ciclo de coordinación."""

    phase: CoordinationPhase
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "message": self.message,
        }


@dataclass
class CoordinationProcess:
    """
    Representa un proceso de coordinación independiente.

    Preparado para múltiples procesos simultáneos en etapas futuras.
    """

    process_id: UUID = field(default_factory=uuid4)
    state: CoordinatorState = CoordinatorState.INICIALIZADO
    current_phase: CoordinationPhase | None = None
    phases: list[PhaseRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "state": self.state.value,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "phases": [p.to_dict() for p in self.phases],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CoordinationResult:
    """Resultado de un ciclo de coordinación — sin datos de negocio."""

    process_id: UUID
    success: bool
    state: CoordinatorState
    message: str
    phases_completed: list[CoordinationPhase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "success": self.success,
            "state": self.state.value,
            "message": self.message,
            "phases_completed": [p.value for p in self.phases_completed],
            "metadata": self.metadata,
        }
