"""Servicio del módulo de Registro de Eventos — fachada sobre EventManager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.events.models import MotorEvent
from zovrake_motor.events.port import EventsPort
from zovrake_motor.models.ports import ModulePort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class EventService(ConfigurationAccessible, ModulePort, EventsPort):
    """
    Módulo de Registro de Eventos.

    Delega en EventManager — el Coordinator coordina el registro de eventos.
    """

    MODULE_NAME = "events"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        event_manager: EventManager | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        max_events = self._events_settings().max_events_in_memory
        self._manager = event_manager or EventManager(max_events_per_process=max_events)
        self._initialized = False

    @property
    def event_manager(self) -> EventManager:
        return self._manager

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._manager._max_events_per_process = self._events_settings().max_events_in_memory
        self._initialized = True

    def emit(
        self,
        *,
        category: EventCategory,
        message: str,
        module: str,
        process_id: UUID,
        event_type: EventType = EventType.MODULE,
        severity: EventSeverity = EventSeverity.INFO,
        associated_state: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> MotorEvent:
        return self._manager.create_and_register(
            process_id=process_id,
            module=module,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=payload,
            category=category,
            severity=severity,
        )

    def get_by_process(self, process_id: UUID) -> list[MotorEvent]:
        return self._manager.get_process_history(process_id)

    def count(self) -> int:
        return self._manager.count()
