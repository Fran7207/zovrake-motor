"""Communication Contracts — catálogo de contratos de la API Interna."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.internal_api.contracts.v1 import contract_snapshot
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.registry import ComponentRegistry


class CommunicationContracts(EnterpriseIntegrationComponentPort):
    """Expone el catálogo de contratos internos — Contract First Design."""

    def __init__(self, *, registry: ComponentRegistry | None = None) -> None:
        self._registry = registry
        self._initialized = False

    @property
    def component_name(self) -> str:
        return "communication_contracts"

    @property
    def component_label(self) -> str:
        return "Communication Contracts"

    def initialize(self) -> None:
        self._initialized = True

    def is_ready(self) -> bool:
        return self._initialized

    def contract_catalog(self) -> dict[str, Any]:
        gateway = None
        if self._registry is not None:
            component = self._registry.get("api_gateway_internal")
            if component is not None and hasattr(component, "internal_api"):
                gateway = component.internal_api

        catalog = {
            "versioning": ContractVersionRegistry.snapshot(),
            "v1": contract_snapshot(),
        }
        if gateway is not None:
            catalog["internal_api"] = gateway.contract_catalog()
        return catalog

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["contract_catalog"] = self.contract_catalog()
        return base
