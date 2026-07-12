"""Componente Security, Validation & Audit Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.svaf.framework import SecurityValidationAuditFramework

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class SecurityValidationAuditFrameworkComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del SVAF.

    Ningún otro componente asume validación estructural, integridad ni auditoría.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        framework: SecurityValidationAuditFramework | None = None,
    ) -> None:
        if integration is None and framework is None:
            raise ValueError("Se requiere integration o framework")
        self._framework = framework or SecurityValidationAuditFramework(
            integration=integration,  # type: ignore[arg-type]
        )

    @property
    def component_name(self) -> str:
        return "security_validation_audit_framework"

    @property
    def component_label(self) -> str:
        return "Security, Validation & Audit Framework"

    @property
    def framework(self) -> SecurityValidationAuditFramework:
        return self._framework

    def initialize(self) -> None:
        self._framework.initialize()

    def is_ready(self) -> bool:
        return self._framework.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["framework"] = self._framework.snapshot()
        base["audits"] = self._framework.audit_store.snapshot()
        return base
