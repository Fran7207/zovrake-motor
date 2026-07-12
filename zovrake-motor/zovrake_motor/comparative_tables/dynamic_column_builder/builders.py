"""Utilidades de construcción de columnas dinámicas."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_column_builder.enums import ColumnDataType
from zovrake_motor.comparative_tables.dynamic_column_builder.gateway import (
    StructureCatalogView,
    StructureView,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeTableColumnCatalog,
    ComparativeTableColumnDefinition,
    ComparativeTableColumnSet,
    ComparativeTableColumnTraceability,
)
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


def infer_data_type(value: Any) -> ColumnDataType:
    if isinstance(value, bool):
        return ColumnDataType.BOOLEAN
    if isinstance(value, int) and not isinstance(value, bool):
        return ColumnDataType.INTEGER
    if isinstance(value, float):
        return ColumnDataType.NUMBER
    if isinstance(value, (list, tuple)):
        return ColumnDataType.LIST
    return ColumnDataType.STRING


def extract_attribute_candidates(
    available_attributes: dict[str, Any],
) -> list[tuple[str, str, ColumnDataType, Any]]:
    """
    Extrae candidatos de atributos desde el snapshot del CSE.

    Retorna tuplas (nombre, fuente, tipo, valor_referencia).
    """
    candidates: list[tuple[str, str, ColumnDataType, Any]] = []
    seen_names: set[str] = set()

    commercial = dict(available_attributes.get("commercial", {}))
    for name, value in sorted(commercial.items()):
        normalized = str(name).strip().lower()
        if not normalized or normalized in seen_names:
            continue
        seen_names.add(normalized)
        candidates.append((str(name), "commercial", infer_data_type(value), value))

    technical = dict(available_attributes.get("technical", {}))
    for name, value in sorted(technical.items()):
        normalized = str(name).strip().lower()
        if not normalized or normalized in seen_names:
            continue
        seen_names.add(normalized)
        candidates.append((str(name), "technical", infer_data_type(value), value))

    specifications = available_attributes.get("specifications", [])
    if isinstance(specifications, list):
        for specification in specifications:
            name = str(specification).strip()
            normalized = name.lower()
            if not normalized or normalized in seen_names:
                continue
            seen_names.add(normalized)
            candidates.append((name, "specification", ColumnDataType.SPECIFICATION, specification))

    primary_item = str(available_attributes.get("primary_item", "")).strip()
    if primary_item:
        normalized = primary_item.lower()
        if normalized not in seen_names:
            seen_names.add(normalized)
            candidates.append((primary_item, "primary_item", ColumnDataType.STRING, primary_item))

    return candidates


def build_public_column_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_column_id(table_id: str, sequence: int) -> str:
    return f"dcb://{table_id}/column-{sequence:04d}"


def build_column_traceability(
    *,
    catalog_view: StructureCatalogView,
    structure_view: StructureView,
    attribute_source: str,
) -> ComparativeTableColumnTraceability:
    return ComparativeTableColumnTraceability(
        process_id=catalog_view.process_id,
        document_id=catalog_view.document_id,
        model_id=catalog_view.model_id,
        source_structure_catalog_id=catalog_view.catalog_id,
        source_table_id=structure_view.table_id,
        source_group_id=structure_view.group_id,
        source_comparative_model_id=structure_view.comparative_model_id,
        attribute_source=attribute_source,
        structure_catalog_preserved=True,
        domain_model_preserved=catalog_view.domain_model_preserved,
    )


def build_column_definition(
    *,
    catalog_view: StructureCatalogView,
    structure_view: StructureView,
    attribute_name: str,
    attribute_source: str,
    data_type: ColumnDataType,
    logical_position: int,
    public_column_id: str,
    internal_sequence: int,
    reference_value: Any,
    settings: DynamicColumnBuilderSettings,
) -> ComparativeTableColumnDefinition:
    return ComparativeTableColumnDefinition(
        column_id=public_column_id,
        internal_column_id=build_internal_column_id(structure_view.table_id, internal_sequence),
        attribute_name=attribute_name,
        data_type=data_type,
        logical_position=logical_position,
        group_id=structure_view.group_id,
        table_id=structure_view.table_id,
        traceability=build_column_traceability(
            catalog_view=catalog_view,
            structure_view=structure_view,
            attribute_source=attribute_source,
        ),
        metadata={
            "column_id_prefix": settings.column_id_prefix,
            "column_id_immutable": settings.column_id_immutable,
            "attribute_source": attribute_source,
            "reference_value_type": type(reference_value).__name__,
            "provider_values_prepared": False,
        },
    )


def build_column_set_for_structure(
    *,
    catalog_view: StructureCatalogView,
    structure_view: StructureView,
    settings: DynamicColumnBuilderSettings,
    start_sequence: int,
) -> tuple[ComparativeTableColumnSet, int]:
    candidates = extract_attribute_candidates(structure_view.available_attributes)
    columns: list[ComparativeTableColumnDefinition] = []
    sequence = start_sequence

    for position, (name, source, data_type, reference_value) in enumerate(candidates, start=1):
        public_column_id = build_public_column_id(
            sequence,
            prefix=settings.column_id_prefix,
            padding=settings.column_id_padding,
        )
        columns.append(
            build_column_definition(
                catalog_view=catalog_view,
                structure_view=structure_view,
                attribute_name=name,
                attribute_source=source,
                data_type=data_type,
                logical_position=position,
                public_column_id=public_column_id,
                internal_sequence=sequence,
                reference_value=reference_value,
                settings=settings,
            ),
        )
        sequence += 1

    column_set = ComparativeTableColumnSet(
        table_id=structure_view.table_id,
        group_id=structure_view.group_id,
        columns=tuple(columns),
        source_structure_catalog_id=catalog_view.catalog_id,
    )
    return column_set, sequence


def build_column_catalog(
    *,
    catalog_view: StructureCatalogView,
    column_sets: tuple[ComparativeTableColumnSet, ...],
    dynamic_row_builder_prepared: bool,
) -> ComparativeTableColumnCatalog:
    return ComparativeTableColumnCatalog(
        catalog_id=f"dcb-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_structure_catalog_id=catalog_view.catalog_id,
        column_sets=column_sets,
        dynamic_row_builder_prepared=dynamic_row_builder_prepared,
        structure_catalog_preserved=True,
        domain_model_preserved=catalog_view.domain_model_preserved,
    )
