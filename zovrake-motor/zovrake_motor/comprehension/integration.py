"""Integración del módulo con configuración, estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.config.categories.comprehension import ComprehensionSettings
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComprehensionMotorIntegration:
    """
    Puente de integración con infraestructura central del Motor.

    No genera eventos ni modifica estados en esta etapa.
    """

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

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    def comprehension_settings(self) -> ComprehensionSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension()
        return ComprehensionSettings.default()

    def is_enabled(self) -> bool:
        return self.comprehension_settings().enabled

    def snapshot(self) -> dict[str, Any]:
        settings = self.comprehension_settings()
        return {
            "enabled": settings.enabled,
            "max_documents_per_process": settings.max_documents_per_process,
            "supported_formats": list(settings.supported_formats),
            "state_management_ready": self._state_manager is not None,
            "event_management_ready": self._event_manager is not None,
        }
