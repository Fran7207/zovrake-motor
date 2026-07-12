"""Organizadores especializados del Provider Organization Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.provider_organization_engine.builders import (
    build_provider_set_for_row_set,
    resolve_structure_for_row_set,
)
from zovrake_motor.comparative_tables.provider_organization_engine.enums import (
    ProviderOrganizerStrategyType,
)
from zovrake_motor.comparative_tables.provider_organization_engine.gateway import (
    ProviderOrganizationInputView,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationIncident,
    ProviderOrganizerResult,
)
from zovrake_motor.comparative_tables.provider_organization_engine.port import ProviderOrganizerPort
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings


class GroupProviderOrganizer(ProviderOrganizerPort):
    """
    Organiza proveedores por Grupo Comparable de forma determinística.

    Cada proveedor permanece asociado únicamente a su grupo y fila correspondiente.
    """

    @property
    def organizer_name(self) -> str:
        return "group_provider_organizer"

    @property
    def organizer_label(self) -> str:
        return "Organizador de Proveedores — Por Grupo Comparable"

    @property
    def organizer_type(self) -> ProviderOrganizerStrategyType:
        return ProviderOrganizerStrategyType.GROUP_PROVIDER

    def organize(
        self,
        input_view: ProviderOrganizationInputView,
        *,
        settings: ProviderOrganizationEngineSettings,
        start_sequence: int,
    ) -> ProviderOrganizerResult:
        provider_sets = []
        incidents: list[ProviderOrganizationIncident] = []
        incident_buffer: list[dict] = []
        sequence = start_sequence

        structures_by_table = {
            structure.table_id: structure
            for structure in input_view.structure_catalog.structures
        }

        for row_set in input_view.row_catalog.row_sets:
            structure_view = resolve_structure_for_row_set(
                row_set=row_set,
                structures_by_table=structures_by_table,
            )
            if structure_view is None:
                incidents.append(
                    ProviderOrganizationIncident(
                        organizer_name=self.organizer_name,
                        message=(
                            f"No se encontró estructura para table_id={row_set.table_id} "
                            f"group_id={row_set.group_id}"
                        ),
                        severity="warning",
                    ),
                )
                continue

            provider_set, sequence = build_provider_set_for_row_set(
                input_view=input_view,
                row_set=row_set,
                structure_view=structure_view,
                settings=settings,
                start_sequence=sequence,
                incidents=incident_buffer,
                organizer_name=self.organizer_name,
            )
            provider_sets.append(provider_set)

        for incident_data in incident_buffer:
            incidents.append(ProviderOrganizationIncident(**incident_data))

        total_providers = sum(len(provider_set.providers) for provider_set in provider_sets)
        return ProviderOrganizerResult(
            organizer_type=self.organizer_type.value,
            organizer_name=self.organizer_name,
            provider_sets=tuple(provider_sets),
            incidents=tuple(incidents),
            technical_observations=(
                f"organizer_type={self.organizer_type.value}",
                f"provider_sets_organized={len(provider_sets)}",
                f"providers_organized={total_providers}",
                f"row_sets_consumed={len(input_view.row_catalog.row_sets)}",
            ),
        )
