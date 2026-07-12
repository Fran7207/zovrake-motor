"""Integration Event Manager — eventos de integración empresarial."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort


class IntegrationEventManager(EnterpriseIntegrationComponentPort):
    """Gestionará eventos de integración — sin persistencia en 8.1."""

    @property
    def component_name(self) -> str:
        return "integration_event_manager"

    @property
    def component_label(self) -> str:
        return "Integration Event Manager"

    def initialize(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True
