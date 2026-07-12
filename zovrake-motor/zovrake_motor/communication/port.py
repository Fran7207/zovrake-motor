"""Contrato del módulo de Comunicación."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.models.common import MotorResponse


class CommunicationPort(ABC):
    """Punto de entrada para comunicación con el ERP."""

    @abstractmethod
    def send(self, response: MotorResponse) -> None:
        """Enviará respuestas al ERP — sin HTTP en esta etapa."""

    @abstractmethod
    def format_response(self, response: MotorResponse) -> dict[str, Any]:
        """Serializará respuestas para transporte futuro."""
