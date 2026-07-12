"""Contrato del módulo de Recepción."""

from __future__ import annotations

from abc import ABC, abstractmethod

from zovrake_motor.models.common import MotorRequest
from zovrake_motor.reception.models import ReceptionResult


class ReceptionPort(ABC):
    """Punto de entrada para recepción de solicitudes del ERP."""

    @abstractmethod
    def receive(self, request: MotorRequest) -> ReceptionResult:
        """Recibirá solicitudes — sin procesamiento en esta etapa."""
