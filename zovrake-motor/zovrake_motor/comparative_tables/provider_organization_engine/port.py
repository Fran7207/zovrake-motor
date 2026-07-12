"""Contrato base de organizadores del Provider Organization Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.provider_organization_engine.enums import (
    ProviderOrganizerStrategyType,
)
from zovrake_motor.comparative_tables.provider_organization_engine.gateway import (
    ProviderOrganizationInputView,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import ProviderOrganizerResult
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings


class ProviderOrganizerPort(ABC):
    """Contrato común para organizadores de proveedores."""

    @property
    @abstractmethod
    def organizer_name(self) -> str:
        """Identificador único del organizador."""

    @property
    @abstractmethod
    def organizer_label(self) -> str:
        """Etiqueta descriptiva del organizador."""

    @property
    @abstractmethod
    def organizer_type(self) -> ProviderOrganizerStrategyType:
        """Tipo de estrategia de organización."""

    @abstractmethod
    def organize(
        self,
        input_view: ProviderOrganizationInputView,
        *,
        settings: ProviderOrganizationEngineSettings,
        start_sequence: int,
    ) -> ProviderOrganizerResult:
        """Organiza proveedores — sin modificar catálogos de entrada."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "organizer_name": self.organizer_name,
            "organizer_label": self.organizer_label,
            "organizer_type": self.organizer_type.value,
        }
