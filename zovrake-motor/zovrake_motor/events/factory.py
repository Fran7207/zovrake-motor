"""Generación de eventos sin administración directa."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.models import MotorEvent


class EventFactory:
    """
    Fábrica de eventos para módulos del Motor.

    Los módulos pueden generar eventos; el Coordinator coordina su registro.
    """

    @staticmethod
    def create(
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
