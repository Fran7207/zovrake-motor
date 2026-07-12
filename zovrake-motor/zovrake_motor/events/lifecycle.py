"""Ciclo de vida conceptual de eventos — sin reglas automáticas."""

from __future__ import annotations

from zovrake_motor.events.enums import EventLifecycleState, EventType


class EventLifecycle:
    """Referencia arquitectónica del ciclo de vida de eventos."""

    LIFECYCLE_STATES: tuple[EventLifecycleState, ...] = (
        EventLifecycleState.CREATED,
        EventLifecycleState.REGISTERED,
        EventLifecycleState.FINALIZED,
    )

    OFFICIAL_TYPES: tuple[EventType, ...] = tuple(EventType)

    def is_valid_type(self, event_type: EventType) -> bool:
        return event_type in self.OFFICIAL_TYPES
