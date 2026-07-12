"""Acceso a configuración centralizada para módulos del Motor."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ConfigurationAccessible:
    """
    Mixin que permite a los módulos consultar la configuración centralizada.

    No almacena parámetros de configuración propios.
    """

    def __init__(self, *, config_provider: ConfigurationProvider | None = None) -> None:
        self._config_provider = config_provider

    @property
    def config_provider(self) -> ConfigurationProvider | None:
        return self._config_provider

    def _events_settings(self):
        from zovrake_motor.config.categories.events import EventsSettings

        if self._config_provider is not None:
            return self._config_provider.events()
        return EventsSettings.default()

    def _communication_settings(self):
        from zovrake_motor.config.categories.communication import CommunicationSettings

        if self._config_provider is not None:
            return self._config_provider.communication()
        return CommunicationSettings.default()

    def _paths_settings(self):
        from zovrake_motor.config.categories.paths import PathsSettings

        if self._config_provider is not None:
            return self._config_provider.paths()
        return PathsSettings.default()
