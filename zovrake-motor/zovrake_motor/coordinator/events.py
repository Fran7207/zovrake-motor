"""Preparación para eventos internos del Coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from zovrake_motor.coordinator.enums import CoordinationPhase, CoordinatorState


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CoordinatorEvent:
    """Evento interno del Coordinator — preparado para sistema de eventos futuro."""

    event_type: str
    message: str
    state: CoordinatorState | None = None
    phase: CoordinationPhase | None = None
    process_id: UUID | None = None
    occurred_at: datetime = field(default_factory=_utc_now)
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "message": self.message,
            "state": self.state.value if self.state else None,
            "phase": self.phase.value if self.phase else None,
            "process_id": str(self.process_id) if self.process_id else None,
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload,
        }


CoordinatorEventHandler = Callable[[CoordinatorEvent], None]


class EventCollector:
    """
    Recolector de eventos en memoria.

    Sustituible por el módulo de eventos en implementaciones futuras.
    """

    def __init__(self) -> None:
        self._handlers: list[CoordinatorEventHandler] = []
        self._events: list[CoordinatorEvent] = []

    def subscribe(self, handler: CoordinatorEventHandler) -> None:
        self._handlers.append(handler)

    def emit(self, event: CoordinatorEvent) -> CoordinatorEvent:
        self._events.append(event)
        for handler in self._handlers:
            handler(event)
        return event

    def emit_state_change(
        self,
        *,
        from_state: CoordinatorState,
        to_state: CoordinatorState,
        message: str,
        process_id: UUID | None = None,
    ) -> CoordinatorEvent:
        return self.emit(CoordinatorEvent(
            event_type="state_change",
            message=message,
            state=to_state,
            process_id=process_id,
            payload={"from_state": from_state.value, "to_state": to_state.value},
        ))

    def get_events(self) -> list[CoordinatorEvent]:
        return list(self._events)

    def count(self) -> int:
        return len(self._events)
