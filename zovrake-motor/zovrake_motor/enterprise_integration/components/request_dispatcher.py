"""Request Dispatcher — despacho de solicitudes ERP hacia el Motor."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort


class RequestDispatcher(EnterpriseIntegrationComponentPort):
    """Despachará solicitudes del ERP hacia el Motor — sin lógica en 8.1."""

    @property
    def component_name(self) -> str:
        return "request_dispatcher"

    @property
    def component_label(self) -> str:
        return "Request Dispatcher"

    def initialize(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True
