"""Modelos del Sistema Central de Gestión de Estados."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.states.enums import MotorState


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StateTransition:
    """Registro de una transición de estado — preparado para observabilidad futura."""

    from_state: MotorState | None
    to_state: MotorState
    reason: str
    occurred_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_state": self.from_state.value if self.from_state else None,
            "to_state": self.to_state.value,
            "reason": self.reason,
            "occurred_at": self.occurred_at.isoformat(),
        }


@dataclass
class ProcessStateRecord:
    """Estado independiente de una solicitud dentro del Motor."""

    process_id: UUID
    current_state: MotorState
    codigo_req: str
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    history: list[StateTransition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "current_state": self.current_state.value,
            "codigo_req": self.codigo_req,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "transition_count": len(self.history),
            "metadata": self.metadata,
        }
