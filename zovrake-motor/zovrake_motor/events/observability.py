"""Preparación para observabilidad futura de eventos."""

from __future__ import annotations

from typing import Protocol

from zovrake_motor.events.models import MotorEvent


class EventObserver(Protocol):
    """Contrato para observadores — monitoreo, auditoría y métricas futuras."""

    def on_event_registered(self, event: MotorEvent) -> None:
        """Notifica el registro de un evento sin ejecutar lógica de negocio."""

    def on_event_finalized(self, event: MotorEvent) -> None:
        """Notifica la finalización de un evento."""
