"""Servicio del módulo de Gestión del Contexto."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.context.models import ProcessContext
from zovrake_motor.context.port import ContextPort
from zovrake_motor.models.common import MotorRequest
from zovrake_motor.models.ports import ModulePort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ContextService(ConfigurationAccessible, ModulePort, ContextPort):
    """
    Módulo de Gestión del Contexto.

    Responsabilidad única: administrar 'Detalles del requerimiento'.
    Sin interpretación ni uso de la información en esta etapa.
    """

    MODULE_NAME = "context"

    def __init__(self, *, config_provider: ConfigurationProvider | None = None) -> None:
        super().__init__(config_provider=config_provider)
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._initialized = True

    def prepare(self, request: MotorRequest) -> ProcessContext:
        return ProcessContext(
            process_id=request.process_id,
            codigo_req=request.codigo_req,
            detalles_requerimiento=request.detalles_requerimiento,
            metadata=dict(request.metadata),
        )
