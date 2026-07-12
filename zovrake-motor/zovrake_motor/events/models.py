"""Modelo uniforme de eventos del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.events.enums import (
    EventCategory,
    EventLifecycleState,
    EventSeverity,
    EventType,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MotorEvent:
    """
    Evento interno uniforme del Motor Inteligente.

    Estructura definitiva preparada para observabilidad y auditoría futuras.
    """

    event_id: UUID
    process_id: UUID
    module: str
    event_type: EventType
    message: str
    occurred_at: datetime = field(default_factory=_utc_now)
    associated_state: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    lifecycle_state: EventLifecycleState = EventLifecycleState.CREATED
    category: EventCategory = EventCategory.SYSTEM
    severity: EventSeverity = EventSeverity.INFO

    @classmethod
    def create(
        cls,
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
        """Genera un evento sin registrarlo — uso por módulos y Coordinator."""
        return cls(
            event_id=uuid4(),
            process_id=process_id,
            module=module,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=dict(metadata or {}),
            lifecycle_state=EventLifecycleState.CREATED,
            category=category,
            severity=severity,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "process_id": str(self.process_id),
            "module": self.module,
            "event_type": self.event_type.value,
            "message": self.message,
            "occurred_at": self.occurred_at.isoformat(),
            "associated_state": self.associated_state,
            "metadata": self.metadata,
            "lifecycle_state": self.lifecycle_state.value,
            "category": self.category.value,
            "severity": self.severity.value,
        }
