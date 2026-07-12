"""API Gateway Interno — host de la API Interna del Motor Inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.internal_api.api import InternalIntegrationApi
from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class ApiGatewayInternal(EnterpriseIntegrationComponentPort):
    """
    Punto de entrada interno de la API del Motor.

    En 8.2 aloja la InternalIntegrationApi. El acceso externo debe
    enrutarse exclusivamente a través del Enterprise Integration Coordinator.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
    ) -> None:
        self._integration = integration
        self._internal_api: InternalIntegrationApi | None = None
        self._initialized = False

    @property
    def component_name(self) -> str:
        return "api_gateway_internal"

    @property
    def component_label(self) -> str:
        return "API Gateway Interno"

    @property
    def internal_api(self) -> InternalIntegrationApi | None:
        return self._internal_api

    def initialize(self) -> None:
        if self._integration is not None:
            context = InternalApiContext(
                config_provider=self._integration.config_provider,
                state_manager=self._integration.state_manager,
                event_manager=self._integration.event_manager,
            )
        else:
            context = InternalApiContext()
        self._internal_api = InternalIntegrationApi(context=context)
        self._internal_api.initialize()
        self._initialized = True

    def is_ready(self) -> bool:
        return (
            self._initialized
            and self._internal_api is not None
            and self._internal_api.is_ready()
        )

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["internal_api"] = (
            self._internal_api.snapshot() if self._internal_api is not None else None
        )
        return base
