"""Preparación para observabilidad futura de cambios de estado."""

from __future__ import annotations

from typing import Protocol

from zovrake_motor.states.models import ProcessStateRecord, StateTransition


class StateChangeObserver(Protocol):
    """Contrato para observadores de transiciones — eventos y métricas futuras."""

    def on_state_change(
        self,
        record: ProcessStateRecord,
        transition: StateTransition,
    ) -> None:
        """Notifica un cambio de estado sin ejecutar lógica de negocio."""
