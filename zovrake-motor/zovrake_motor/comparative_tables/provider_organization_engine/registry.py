"""Registro centralizado de organizadores del POE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.provider_organization_engine.exceptions import (
    ProviderOrganizerNotFoundError,
)
from zovrake_motor.comparative_tables.provider_organization_engine.organizers_strategies import (
    GroupProviderOrganizer,
)
from zovrake_motor.comparative_tables.provider_organization_engine.port import ProviderOrganizerPort
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings


class ProviderOrganizerRegistry:
    """
    Registro único de organizadores de proveedores.

    Todo organizador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._organizers_by_name: dict[str, ProviderOrganizerPort] = {}
        self._organizers_ordered: list[ProviderOrganizerPort] = []

    def register(self, organizer: ProviderOrganizerPort) -> None:
        if organizer.organizer_name in self._organizers_by_name:
            raise ValueError(f"Organizador ya registrado: {organizer.organizer_name}")
        self._organizers_by_name[organizer.organizer_name] = organizer
        self._organizers_ordered.append(organizer)

    def register_defaults(
        self,
        *,
        settings: ProviderOrganizationEngineSettings | None = None,
    ) -> None:
        settings = settings or ProviderOrganizationEngineSettings.default()
        candidates: list[tuple[bool, ProviderOrganizerPort]] = [
            (settings.group_provider_organizer_enabled, GroupProviderOrganizer()),
        ]
        for enabled, organizer in candidates:
            if enabled:
                self.register(organizer)

    def get(self, name: str) -> ProviderOrganizerPort | None:
        return self._organizers_by_name.get(name)

    def require(self, name: str) -> ProviderOrganizerPort:
        organizer = self.get(name)
        if organizer is None:
            raise ProviderOrganizerNotFoundError(f"Organizador no registrado: {name}")
        return organizer

    def all_organizers(self) -> tuple[ProviderOrganizerPort, ...]:
        return tuple(self._organizers_ordered)

    def count(self) -> int:
        return len(self._organizers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [organizer.snapshot() for organizer in self._organizers_ordered]
