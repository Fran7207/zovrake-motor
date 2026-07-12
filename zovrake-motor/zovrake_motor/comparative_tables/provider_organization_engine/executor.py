"""Ejecutor de organizadores del Provider Organization Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.provider_organization_engine.builders import (
    build_organized_provider_catalog,
)
from zovrake_motor.comparative_tables.provider_organization_engine.enums import (
    ProviderOrganizationBuildStatus,
)
from zovrake_motor.comparative_tables.provider_organization_engine.gateway import (
    ProviderOrganizationInputView,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    OrganizedProviderSet,
    ProviderOrganizationBuildResult,
    ProviderOrganizationIncident,
)
from zovrake_motor.comparative_tables.provider_organization_engine.registry import (
    ProviderOrganizerRegistry,
)
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings


class ProviderOrganizationExecutor:
    """Coordina la ejecución secuencial de organizadores sin modificar catálogos de entrada."""

    def __init__(self, registry: ProviderOrganizerRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ProviderOrganizationInputView,
        *,
        settings: ProviderOrganizationEngineSettings,
    ) -> ProviderOrganizationBuildResult:
        provider_sets: list[OrganizedProviderSet] = []
        incidents: list[ProviderOrganizationIncident] = []
        observations: list[str] = []
        sequence = 1

        for organizer in self._registry.all_organizers():
            result = organizer.organize(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            provider_sets.extend(result.provider_sets)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += sum(
                len(provider_set.providers) for provider_set in result.provider_sets
            )

        total_providers = sum(len(provider_set.providers) for provider_set in provider_sets)
        if total_providers > settings.max_providers_per_organization:
            incidents.append(
                ProviderOrganizationIncident(
                    organizer_name="provider_organization_executor",
                    message=(
                        f"Se organizaron {total_providers} proveedores; "
                        f"límite configurado: {settings.max_providers_per_organization}"
                    ),
                    severity="warning",
                ),
            )
            trimmed_sets: list[OrganizedProviderSet] = []
            remaining = settings.max_providers_per_organization
            for provider_set in provider_sets:
                if remaining <= 0:
                    break
                providers = provider_set.providers[:remaining]
                remaining -= len(providers)
                trimmed_sets.append(
                    OrganizedProviderSet(
                        table_id=provider_set.table_id,
                        group_id=provider_set.group_id,
                        providers=providers,
                        source_structure_catalog_id=provider_set.source_structure_catalog_id,
                        source_column_catalog_id=provider_set.source_column_catalog_id,
                        source_row_catalog_id=provider_set.source_row_catalog_id,
                    ),
                )
            provider_sets = trimmed_sets

        catalog = build_organized_provider_catalog(
            input_view=input_view,
            provider_sets=tuple(provider_sets),
            group_integrity_engine_prepared=settings.group_integrity_engine_prepared,
        )

        status = (
            ProviderOrganizationBuildStatus.ORGANIZED
            if provider_sets
            else ProviderOrganizationBuildStatus.SKIPPED
        )
        observations.extend(
            (
                "structure_catalog_preserved=True",
                "column_catalog_preserved=True",
                "row_catalog_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "providers_organized=" + str(total_providers),
            ),
        )

        return ProviderOrganizationBuildResult(
            process_id=input_view.row_catalog.process_id,
            document_id=input_view.row_catalog.document_id,
            model_id=input_view.row_catalog.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            column_catalog_preserved=True,
            structure_catalog_preserved=True,
            row_catalog_preserved=True,
            domain_model_preserved=input_view.row_catalog.domain_model_preserved,
            organizers_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
