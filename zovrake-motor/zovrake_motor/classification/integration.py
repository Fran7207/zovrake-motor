"""Integración del módulo con configuración, estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.config.categories.classification import ClassificationSettings
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ClassificationMotorIntegration:
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

    def classification_settings(self) -> ClassificationSettings:
        if self._config_provider is not None:
            return self._config_provider.classification()
        return ClassificationSettings.default()

    def is_enabled(self) -> bool:
        return self.classification_settings().enabled

    def snapshot(self) -> dict[str, Any]:
        settings = self.classification_settings()
        return {
            "enabled": settings.enabled,
            "max_concepts_per_process": settings.max_concepts_per_process,
            "max_materials_per_process": settings.max_materials_per_process,
            "max_services_per_process": settings.max_services_per_process,
            "comprehension_integration_prepared": settings.comprehension_integration_prepared,
            "state_management_ready": self._state_manager is not None,
            "event_management_ready": self._event_manager is not None,
        }
