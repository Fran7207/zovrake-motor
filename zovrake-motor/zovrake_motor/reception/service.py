"""Servicio del módulo de Recepción."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.models.common import MotorRequest
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.reception.models import ReceptionResult
from zovrake_motor.reception.port import ReceptionPort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ReceptionService(ConfigurationAccessible, ModulePort, ReceptionPort):
    """
    Módulo de Recepción.

    Responsabilidad única: recibir solicitudes provenientes del ERP.
    Sin validaciones ni procesamiento en esta etapa.
    """

    MODULE_NAME = "reception"

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

    def receive(self, request: MotorRequest) -> ReceptionResult:
        return ReceptionResult(
            accepted=True,
            process_id=request.process_id,
            codigo_req=request.codigo_req,
            message="Recepción preparada — sin validación en esta etapa",
        )
