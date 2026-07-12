"""Utilidades de construcción de filas dinámicas."""

from __future__ import annotations

from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import (
    ColumnCatalogView,
    ColumnSetView,
    RowBuildInputView,
    StructureCatalogView,
    StructureView,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeTableCellPlaceholder,
    ComparativeTableRowCatalog,
    ComparativeTableRowDefinition,
    ComparativeTableRowSet,
    ComparativeTableRowTraceability,
)
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings


def build_public_row_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_row_id(table_id: str, sequence: int) -> str:
    return f"drb://{table_id}/row-{sequence:04d}"


def _structure_by_table_id(
    structure_catalog: StructureCatalogView,
) -> dict[str, StructureView]:
    return {structure.table_id: structure for structure in structure_catalog.structures}


def build_row_traceability(
    *,
    input_view: RowBuildInputView,
    column_set: ColumnSetView,
    provider_id: str,
) -> ComparativeTableRowTraceability:
    return ComparativeTableRowTraceability(
        process_id=input_view.column_catalog.process_id,
        document_id=input_view.column_catalog.document_id,
        model_id=input_view.column_catalog.model_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_table_id=column_set.table_id,
        source_group_id=column_set.group_id,
        source_provider_id=provider_id,
        column_catalog_preserved=True,
        structure_catalog_preserved=True,
        domain_model_preserved=input_view.column_catalog.domain_model_preserved,
    )


def build_cell_placeholders(
    column_set: ColumnSetView,
) -> tuple[ComparativeTableCellPlaceholder, ...]:
    return tuple(
        ComparativeTableCellPlaceholder(
            column_id=column.column_id,
            attribute_name=column.attribute_name,
            logical_position=column.logical_position,
            value_prepared=False,
        )
        for column in column_set.columns
    )


def build_row_definition(
    *,
    input_view: RowBuildInputView,
    column_set: ColumnSetView,
    provider_id: str,
    logical_position: int,
    public_row_id: str,
    internal_sequence: int,
    settings: DynamicRowBuilderSettings,
) -> ComparativeTableRowDefinition:
    column_references = tuple(column.column_id for column in column_set.columns)
    cells_reserved = build_cell_placeholders(column_set)

    return ComparativeTableRowDefinition(
        row_id=public_row_id,
        internal_row_id=build_internal_row_id(column_set.table_id, internal_sequence),
        provider_id=provider_id,
        logical_position=logical_position,
        group_id=column_set.group_id,
        table_id=column_set.table_id,
        column_references=column_references,
        cells_reserved=cells_reserved,
        traceability=build_row_traceability(
            input_view=input_view,
            column_set=column_set,
            provider_id=provider_id,
        ),
        metadata={
            "row_id_prefix": settings.row_id_prefix,
            "row_id_immutable": settings.row_id_immutable,
            "cell_values_prepared": False,
            "columns_linked": len(column_references),
        },
    )


def build_row_set_for_column_set(
    *,
    input_view: RowBuildInputView,
    column_set: ColumnSetView,
    structure_view: StructureView,
    settings: DynamicRowBuilderSettings,
    start_sequence: int,
) -> tuple[ComparativeTableRowSet, int]:
    rows: list[ComparativeTableRowDefinition] = []
    sequence = start_sequence
    providers = structure_view.available_providers

    for position, provider_id in enumerate(providers, start=1):
        public_row_id = build_public_row_id(
            sequence,
            prefix=settings.row_id_prefix,
            padding=settings.row_id_padding,
        )
        rows.append(
            build_row_definition(
                input_view=input_view,
                column_set=column_set,
                provider_id=provider_id,
                logical_position=position,
                public_row_id=public_row_id,
                internal_sequence=sequence,
                settings=settings,
            ),
        )
        sequence += 1

    row_set = ComparativeTableRowSet(
        table_id=column_set.table_id,
        group_id=column_set.group_id,
        rows=tuple(rows),
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
    )
    return row_set, sequence


def build_row_catalog(
    *,
    input_view: RowBuildInputView,
    row_sets: tuple[ComparativeTableRowSet, ...],
    provider_organization_engine_prepared: bool,
) -> ComparativeTableRowCatalog:
    return ComparativeTableRowCatalog(
        catalog_id=f"drb-catalog://{input_view.column_catalog.model_id}",
        process_id=input_view.column_catalog.process_id,
        model_id=input_view.column_catalog.model_id,
        document_id=input_view.column_catalog.document_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        row_sets=row_sets,
        provider_organization_engine_prepared=provider_organization_engine_prepared,
        column_catalog_preserved=True,
        structure_catalog_preserved=True,
        domain_model_preserved=input_view.column_catalog.domain_model_preserved,
    )


def resolve_structure_for_column_set(
    *,
    column_set: ColumnSetView,
    structures_by_table: dict[str, StructureView],
) -> StructureView | None:
    structure = structures_by_table.get(column_set.table_id)
    if structure is not None and structure.group_id == column_set.group_id:
        return structure
    return None
