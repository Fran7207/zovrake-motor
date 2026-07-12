"""Componente ERP Communication Gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.ecg.gateway import ErpCommunicationGateway

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class ErpCommunicationGatewayComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del ECG.

    Ningún otro componente intercambia información directamente ERP ↔ Motor.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        gateway: ErpCommunicationGateway | None = None,
    ) -> None:
        if integration is None and gateway is None:
            raise ValueError("Se requiere integration o gateway")
        self._gateway = gateway or ErpCommunicationGateway(integration=integration)  # type: ignore[arg-type]

    @property
    def component_name(self) -> str:
        return "erp_communication_gateway"

    @property
    def component_label(self) -> str:
        return "ERP Communication Gateway"

    @property
    def gateway(self) -> ErpCommunicationGateway:
        return self._gateway

    def initialize(self) -> None:
        self._gateway.initialize()

    def is_ready(self) -> bool:
        return self._gateway.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["gateway"] = self._gateway.snapshot()
        base["messages"] = self._gateway.message_store.snapshot()
        return base
