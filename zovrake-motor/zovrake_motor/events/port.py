"""Contrato del módulo de Registro de Eventos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.models import MotorEvent


class EventsPort(ABC):
    """Punto de entrada para registro de eventos internos."""

    @abstractmethod
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
        """Registrará eventos — sin persistencia en esta etapa."""

    @abstractmethod
    def get_by_process(self, process_id: UUID) -> list[MotorEvent]:
        """Consultará eventos por proceso."""
