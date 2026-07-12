"""Contrato del módulo de Gestión de Estados."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.models import ProcessStateRecord


class StatesPort(ABC):
    """Punto de entrada para administración de estados de procesos."""

    @abstractmethod
    def create_process(self, process_id: UUID, codigo_req: str) -> ProcessStateRecord:
        """Creará un proceso con estado inicial."""

    @abstractmethod
    def get(self, process_id: UUID) -> ProcessStateRecord | None:
        """Consultará el estado de un proceso."""

    @abstractmethod
    def transition(self, process_id: UUID, to_state: MotorState, reason: str) -> ProcessStateRecord:
        """Registrará transiciones — sin reglas complejas en esta etapa."""
