"""
Sistema Central de Gestión de Eventos (EMS) del Motor Inteligente.

Única autoridad para registrar y administrar eventos internos.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.events.enums import (
    EventCategory,
    EventLifecycleState,
    EventSeverity,
    EventType,
)
from zovrake_motor.events.exceptions import EventManagementError, EventNotFoundError
from zovrake_motor.events.lifecycle import EventLifecycle
from zovrake_motor.events.models import MotorEvent
from zovrake_motor.events.observability import EventObserver
from zovrake_motor.events.store import EventStore


class EventManager:
    """
    Administrador central de eventos del Motor.

    No ejecuta procesamiento, no modifica estados ni aplica reglas de negocio.
    """

    def __init__(
        self,
        *,
        store: EventStore | None = None,
        lifecycle: EventLifecycle | None = None,
        max_events_per_process: int | None = None,
    ) -> None:
        self._store = store or EventStore()
        self._lifecycle = lifecycle or EventLifecycle()
        self._max_events_per_process = max_events_per_process
        self._observers: list[EventObserver] = []

    @property
    def store(self) -> EventStore:
        return self._store

    @property
    def lifecycle(self) -> EventLifecycle:
        return self._lifecycle

    def register_observer(self, observer: EventObserver) -> None:
        """Preparado para observabilidad — monitoreo y auditoría futuras."""
        self._observers.append(observer)

    def create_event(
        self,
        *,
        process_id: UUID,
        module: str,
        event_type: EventType,
        message: str,
        associated_state: str | None = None,
        metadata: dict[str, Any] | None = None,
        category: EventCategory = EventCategory.SYSTEM,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> MotorEvent:
        """Crea un evento sin registrarlo en el historial."""
        if not self._lifecycle.is_valid_type(event_type):
            raise EventManagementError(f"Tipo de evento no válido: {event_type.value}")
        return MotorEvent.create(
            process_id=process_id,
            module=module,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=metadata,
            category=category,
            severity=severity,
        )

    def register_event(self, event: MotorEvent) -> MotorEvent:
        """Registra un evento en el historial del proceso."""
        if event.lifecycle_state == EventLifecycleState.FINALIZED:
            raise EventManagementError("No se puede registrar un evento finalizado")

        event.lifecycle_state = EventLifecycleState.REGISTERED
        self._store.append(event)
        self._trim_process_history(event.process_id)
        self._notify_registered(event)
        return event

    def create_and_register(
        self,
        *,
        process_id: UUID,
        module: str,
        event_type: EventType,
        message: str,
        associated_state: str | None = None,
        metadata: dict[str, Any] | None = None,
        category: EventCategory = EventCategory.SYSTEM,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> MotorEvent:
        event = self.create_event(
            process_id=process_id,
            module=module,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=metadata,
            category=category,
            severity=severity,
        )
        return self.register_event(event)

    def finalize_event(self, event_id: UUID) -> MotorEvent:
        event = self._store.require(event_id)
        if event.lifecycle_state == EventLifecycleState.FINALIZED:
            raise EventManagementError(f"El evento ya está finalizado: {event_id}")

        event.lifecycle_state = EventLifecycleState.FINALIZED
        self._notify_finalized(event)
        return event

    def get_event(self, event_id: UUID) -> MotorEvent | None:
        return self._store.get(event_id)

    def require_event(self, event_id: UUID) -> MotorEvent:
        return self._store.require(event_id)

    def get_process_history(self, process_id: UUID) -> list[MotorEvent]:
        return self._store.get_process_history(process_id)

    def count(self) -> int:
        return self._store.count()

    def count_by_process(self, process_id: UUID) -> int:
        return self._store.count_by_process(process_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total_events": self.count(),
            "process_count": len(self._store.list_process_ids()),
            "event_types": [event_type.value for event_type in self._lifecycle.OFFICIAL_TYPES],
            "processes": [
                {
                    "process_id": str(process_id),
                    "event_count": self.count_by_process(process_id),
                }
                for process_id in self._store.list_process_ids()
            ],
        }

    def _trim_process_history(self, process_id: UUID) -> None:
        if self._max_events_per_process is None:
            return
        self._store.trim_process_history(process_id, self._max_events_per_process)

    def _notify_registered(self, event: MotorEvent) -> None:
        for observer in self._observers:
            observer.on_event_registered(event)

    def _notify_finalized(self, event: MotorEvent) -> None:
        for observer in self._observers:
            observer.on_event_finalized(event)
