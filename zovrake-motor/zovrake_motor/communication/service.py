"""Servicio del módulo de Comunicación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.communication.models import OutboundMessage
from zovrake_motor.communication.port import CommunicationPort
from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.models.common import MotorResponse
from zovrake_motor.models.ports import ModulePort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class CommunicationService(ConfigurationAccessible, ModulePort, CommunicationPort):
    """
    Módulo de Comunicación.

    Responsabilidad única: comunicación entre Motor y ERP.
    Sin HTTP, API ni WebSocket en esta etapa.
    """

    MODULE_NAME = "communication"

    def __init__(self, *, config_provider: ConfigurationProvider | None = None) -> None:
        super().__init__(config_provider=config_provider)
        self._initialized = False
        self._outbound: list[OutboundMessage] = []

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._initialized = True

    def send(self, response: MotorResponse) -> None:
        message = OutboundMessage(payload=self.format_response(response))
        self._outbound.append(message)

    def format_response(self, response: MotorResponse) -> dict[str, Any]:
        return {
            "process_id": str(response.process_id),
            "codigo_req": response.codigo_req,
            "success": response.success,
            "message": response.message,
            "metadata": response.metadata,
        }

    @property
    def outbound_count(self) -> int:
        return len(self._outbound)
