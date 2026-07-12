"""Contrato del módulo de Gestión del Contexto."""

from __future__ import annotations

from abc import ABC, abstractmethod

from zovrake_motor.context.models import ProcessContext
from zovrake_motor.models.common import MotorRequest


class ContextPort(ABC):
    """Punto de entrada para administración del contexto del requerimiento."""

    @abstractmethod
    def prepare(self, request: MotorRequest) -> ProcessContext:
        """Preparará el contexto — sin interpretación en esta etapa."""
