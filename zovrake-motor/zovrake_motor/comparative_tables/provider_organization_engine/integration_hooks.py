"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    OrganizedProviderCatalog,
)
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings


class GroupIntegrityEngineIntegrationPoint:
    """Preparación hacia el Group Integrity Engine — sin ejecución."""

    def __init__(self, *, settings: ProviderOrganizationEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_integrity_check(
        self,
        catalog: OrganizedProviderCatalog,
    ) -> dict[str, Any]:
        total_providers = sum(
            len(provider_set.providers) for provider_set in catalog.provider_sets
        )
        return {
            "prepared": self._settings.group_integrity_engine_prepared,
            "provider_sets_count": len(catalog.provider_sets),
            "providers_count": total_providers,
            "status": (
                "prepared"
                if self._settings.group_integrity_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "group_integrity_engine_prepared": self._settings.group_integrity_engine_prepared,
            "status": (
                "prepared"
                if self._settings.group_integrity_engine_prepared
                else "not_prepared"
            ),
        }
