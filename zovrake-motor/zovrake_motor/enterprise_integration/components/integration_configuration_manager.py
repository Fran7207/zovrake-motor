"""Integration Configuration Manager — configuración de integración empresarial."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort


class IntegrationConfigurationManager(EnterpriseIntegrationComponentPort):
    """Gestionará configuración de integración — delega al sistema centralizado."""

    @property
    def component_name(self) -> str:
        return "integration_configuration_manager"

    @property
    def component_label(self) -> str:
        return "Integration Configuration Manager"

    def initialize(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True
