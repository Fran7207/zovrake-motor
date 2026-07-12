"""Utilidades de organización de proveedores."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.provider_organization_engine.gateway import (
    ProviderOrganizationInputView,
    RowDefinitionView,
    RowSetView,
    StructureView,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    OrganizedProviderCatalog,
    OrganizedProviderCommercialInformation,
    OrganizedProviderRecord,
    OrganizedProviderSet,
    OrganizedProviderTechnicalInformation,
    OrganizedProviderTraceability,
)
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings


def build_public_organization_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_organization_id(table_id: str, sequence: int) -> str:
    return f"poe://{table_id}/provider-{sequence:04d}"


def build_document_reference(structure_view: StructureView) -> str:
    lineage = dict(structure_view.traceability.get("lineage", {}))
    document_reference = str(lineage.get("document_reference", "")).strip()
    if document_reference:
        return document_reference
    return structure_view.document_id


def build_provider_traceability(
    *,
    input_view: ProviderOrganizationInputView,
    row_set: RowSetView,
    row_view: RowDefinitionView,
    structure_view: StructureView,
) -> OrganizedProviderTraceability:
    return OrganizedProviderTraceability(
        process_id=input_view.row_catalog.process_id,
        document_id=input_view.row_catalog.document_id,
        model_id=input_view.row_catalog.model_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        source_table_id=row_set.table_id,
        source_group_id=row_set.group_id,
        source_row_id=row_view.row_id,
        source_provider_id=row_view.provider_id,
        source_document_reference=build_document_reference(structure_view),
        column_catalog_preserved=True,
        structure_catalog_preserved=True,
        row_catalog_preserved=True,
        domain_model_preserved=input_view.row_catalog.domain_model_preserved,
    )


def extract_commercial_information(
    structure_view: StructureView,
) -> OrganizedProviderCommercialInformation:
    commercial = dict(structure_view.available_attributes.get("commercial", {}))
    return OrganizedProviderCommercialInformation(fields=commercial)


def extract_technical_information(
    structure_view: StructureView,
) -> OrganizedProviderTechnicalInformation:
    technical = dict(structure_view.available_attributes.get("technical", {}))
    specifications_raw = structure_view.available_attributes.get("specifications", [])
    specifications = (
        tuple(str(spec) for spec in specifications_raw)
        if isinstance(specifications_raw, list)
        else ()
    )
    return OrganizedProviderTechnicalInformation(
        fields=technical,
        specifications=specifications,
    )


def build_organized_provider_record(
    *,
    input_view: ProviderOrganizationInputView,
    row_set: RowSetView,
    row_view: RowDefinitionView,
    structure_view: StructureView,
    logical_position: int,
    public_organization_id: str,
    internal_sequence: int,
    settings: ProviderOrganizationEngineSettings,
) -> OrganizedProviderRecord:
    return OrganizedProviderRecord(
        organization_id=public_organization_id,
        internal_organization_id=build_internal_organization_id(
            row_set.table_id,
            internal_sequence,
        ),
        provider_id=row_view.provider_id,
        group_id=row_set.group_id,
        table_id=row_set.table_id,
        row_id=row_view.row_id,
        row_reference=row_view.row_id,
        document_reference=build_document_reference(structure_view),
        commercial_information=extract_commercial_information(structure_view),
        technical_information=extract_technical_information(structure_view),
        inherited_context=dict(structure_view.inherited_context),
        confidence_level_available=structure_view.confidence_level_available,
        logical_position=logical_position,
        column_references=row_view.column_references,
        traceability=build_provider_traceability(
            input_view=input_view,
            row_set=row_set,
            row_view=row_view,
            structure_view=structure_view,
        ),
        metadata={
            "organization_id_prefix": settings.organization_id_prefix,
            "organization_id_immutable": settings.organization_id_immutable,
            "group_type": structure_view.group_type,
            "comparative_model_id": structure_view.comparative_model_id,
            "provider_data_modified": False,
        },
    )


def sort_rows_deterministically(
    rows: tuple[RowDefinitionView, ...],
    *,
    enabled: bool,
) -> tuple[RowDefinitionView, ...]:
    if not enabled:
        return rows
    return tuple(sorted(rows, key=lambda row: (row.provider_id, row.row_id)))


def build_provider_set_for_row_set(
    *,
    input_view: ProviderOrganizationInputView,
    row_set: RowSetView,
    structure_view: StructureView,
    settings: ProviderOrganizationEngineSettings,
    start_sequence: int,
    incidents: list,
    organizer_name: str,
) -> tuple[OrganizedProviderSet, int]:
    sorted_rows = sort_rows_deterministically(
        row_set.rows,
        enabled=settings.deterministic_sort_enabled,
    )
    providers: list[OrganizedProviderRecord] = []
    seen_providers: set[str] = set()
    sequence = start_sequence

    for position, row_view in enumerate(sorted_rows, start=1):
        normalized_provider = row_view.provider_id.strip().lower()
        if normalized_provider in seen_providers:
            incidents.append(
                {
                    "organizer_name": organizer_name,
                    "message": (
                        f"Proveedor duplicado detectado en grupo {row_set.group_id}: "
                        f"{row_view.provider_id}"
                    ),
                    "severity": "warning",
                },
            )
            continue
        seen_providers.add(normalized_provider)

        public_id = build_public_organization_id(
            sequence,
            prefix=settings.organization_id_prefix,
            padding=settings.organization_id_padding,
        )
        providers.append(
            build_organized_provider_record(
                input_view=input_view,
                row_set=row_set,
                row_view=row_view,
                structure_view=structure_view,
                logical_position=position,
                public_organization_id=public_id,
                internal_sequence=sequence,
                settings=settings,
            ),
        )
        sequence += 1

    provider_set = OrganizedProviderSet(
        table_id=row_set.table_id,
        group_id=row_set.group_id,
        providers=tuple(providers),
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
    )
    return provider_set, sequence


def build_organized_provider_catalog(
    *,
    input_view: ProviderOrganizationInputView,
    provider_sets: tuple[OrganizedProviderSet, ...],
    group_integrity_engine_prepared: bool,
) -> OrganizedProviderCatalog:
    return OrganizedProviderCatalog(
        catalog_id=f"poe-catalog://{input_view.row_catalog.model_id}",
        process_id=input_view.row_catalog.process_id,
        model_id=input_view.row_catalog.model_id,
        document_id=input_view.row_catalog.document_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        provider_sets=provider_sets,
        group_integrity_engine_prepared=group_integrity_engine_prepared,
        column_catalog_preserved=True,
        structure_catalog_preserved=True,
        row_catalog_preserved=True,
        domain_model_preserved=input_view.row_catalog.domain_model_preserved,
    )


def resolve_structure_for_row_set(
    *,
    row_set: RowSetView,
    structures_by_table: dict[str, StructureView],
) -> StructureView | None:
    structure = structures_by_table.get(row_set.table_id)
    if structure is not None and structure.group_id == row_set.group_id:
        return structure
    return None
