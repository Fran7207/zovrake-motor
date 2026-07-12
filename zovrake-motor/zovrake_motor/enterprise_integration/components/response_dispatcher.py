"""Response Dispatcher — despacho de respuestas del Motor hacia el ERP."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort


class ResponseDispatcher(EnterpriseIntegrationComponentPort):
    """Despachará respuestas del Motor hacia el ERP — sin lógica en 8.1."""

    @property
    def component_name(self) -> str:
        return "response_dispatcher"

    @property
    def component_label(self) -> str:
        return "Response Dispatcher"

    def initialize(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True
