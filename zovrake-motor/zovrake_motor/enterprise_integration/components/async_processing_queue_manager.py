"""Componente Async Processing & Queue Manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.apqm.queue_manager import AsyncProcessingQueueManager
from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class AsyncProcessingQueueManagerComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del APQM.

    Ningún otro componente administra procesamiento asíncrono.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        manager: AsyncProcessingQueueManager | None = None,
    ) -> None:
        if integration is None and manager is None:
            raise ValueError("Se requiere integration o manager")
        self._manager = manager or AsyncProcessingQueueManager(integration=integration)  # type: ignore[arg-type]

    @property
    def component_name(self) -> str:
        return "async_processing_queue_manager"

    @property
    def component_label(self) -> str:
        return "Asynchronous Processing & Queue Manager"

    @property
    def manager(self) -> AsyncProcessingQueueManager:
        return self._manager

    def initialize(self) -> None:
        self._manager.initialize()

    def is_ready(self) -> bool:
        return self._manager.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["manager"] = self._manager.snapshot()
        base["queue"] = self._manager.queue_store.snapshot()
        return base
