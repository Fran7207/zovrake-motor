"""Almacenamiento in-memory de eventos por proceso."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.events.exceptions import EventNotFoundError
from zovrake_motor.events.models import MotorEvent


class EventStore:
    """
    Almacén central de eventos — historial independiente por solicitud.

    Preparado para miles de eventos sin compartir historiales entre procesos.
    """

    def __init__(self) -> None:
        self._by_process: dict[UUID, list[MotorEvent]] = {}
        self._by_id: dict[UUID, MotorEvent] = {}

    def append(self, event: MotorEvent) -> None:
        self._by_id[event.event_id] = event
        history = self._by_process.setdefault(event.process_id, [])
        history.append(event)

    def get(self, event_id: UUID) -> MotorEvent | None:
        return self._by_id.get(event_id)

    def require(self, event_id: UUID) -> MotorEvent:
        event = self.get(event_id)
        if event is None:
            raise EventNotFoundError(f"Evento no encontrado: {event_id}")
        return event

    def get_process_history(self, process_id: UUID) -> list[MotorEvent]:
        return list(self._by_process.get(process_id, []))

    def has_process(self, process_id: UUID) -> bool:
        return process_id in self._by_process

    def list_process_ids(self) -> list[UUID]:
        return list(self._by_process.keys())

    def count(self) -> int:
        return len(self._by_id)

    def count_by_process(self, process_id: UUID) -> int:
        return len(self._by_process.get(process_id, []))

    def trim_process_history(self, process_id: UUID, max_events: int) -> None:
        history = self._by_process.get(process_id, [])
        overflow = len(history) - max_events
        if overflow <= 0:
            return
        removed = history[:overflow]
        self._by_process[process_id] = history[overflow:]
        for event in removed:
            self._by_id.pop(event.event_id, None)
