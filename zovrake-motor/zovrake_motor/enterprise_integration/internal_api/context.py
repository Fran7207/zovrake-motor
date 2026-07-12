"""Contexto de ejecución de la API Interna — configuración, estados y eventos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.config.categories.enterprise_integration import InternalIntegrationApiSettings
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class InternalApiContext:
    """
    Contexto compartido de la API Interna.

    Obtiene configuración exclusivamente del Sistema Centralizado de Configuración.
    """

    MODULE_NAME = "InternalIntegrationApi"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._state_manager = state_manager or StateManager()
        self._event_manager = event_manager or EventManager()
        self._initialized = False

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    def settings(self) -> InternalIntegrationApiSettings:
        if self._config_provider is not None:
            return self._config_provider.enterprise_integration().internal_integration_api
        from zovrake_motor.config.categories.enterprise_integration import (
            InternalIntegrationApiSettings,
        )

        return InternalIntegrationApiSettings.default()

    def initialize(self) -> None:
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def snapshot(self) -> dict[str, Any]:
        settings = self.settings()
        return {
            "initialized": self._initialized,
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "active_contract_version": settings.active_contract_version,
            "structural_validation_enabled": settings.structural_validation_enabled,
            "state_management_ready": self._state_manager is not None,
            "event_management_ready": self._event_manager is not None,
        }
