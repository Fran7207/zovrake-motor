"""Error Management Framework — marco de gestión de errores de integración."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort


class ErrorManagementFramework(EnterpriseIntegrationComponentPort):
    """Gestionará errores de integración — sin lógica en 8.1."""

    @property
    def component_name(self) -> str:
        return "error_management_framework"

    @property
    def component_label(self) -> str:
        return "Error Management Framework"

    def initialize(self) -> None:
        pass

    def is_ready(self) -> bool:
        return True
