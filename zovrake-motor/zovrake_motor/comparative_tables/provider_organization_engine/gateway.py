"""Gateway de consumo de catálogos del CSE, DCB y DRB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.provider_organization_engine.exceptions import (
    ColumnCatalogAccessError,
    RowCatalogAccessError,
    StructureCatalogAccessError,
)


@dataclass(frozen=True)
class RowDefinitionView:
    """Vista de solo lectura de una fila dinámica."""

    row_id: str
    provider_id: str
    logical_position: int
    group_id: str
    table_id: str
    column_references: tuple[str, ...]


@dataclass(frozen=True)
class RowSetView:
    """Vista de solo lectura de un conjunto de filas."""

    table_id: str
    group_id: str
    rows: tuple[RowDefinitionView, ...]
    source_structure_catalog_id: str
    source_column_catalog_id: str


@dataclass(frozen=True)
class RowCatalogView:
    """Vista de solo lectura del catálogo de filas dinámicas."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    row_sets: tuple[RowSetView, ...]
    provider_organization_engine_prepared: bool
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class ColumnDefinitionView:
    """Vista de solo lectura de una columna dinámica."""

    column_id: str
    attribute_name: str
    group_id: str
    table_id: str


@dataclass(frozen=True)
class ColumnSetView:
    """Vista de solo lectura de un conjunto de columnas."""

    table_id: str
    group_id: str
    columns: tuple[ColumnDefinitionView, ...]


@dataclass(frozen=True)
class ColumnCatalogView:
    """Vista de solo lectura del catálogo de columnas dinámicas."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    column_sets: tuple[ColumnSetView, ...]
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class StructureView:
    """Vista de solo lectura de una estructura base del CSE."""

    table_id: str
    group_id: str
    group_type: str
    document_id: str
    comparative_model_id: str
    available_providers: tuple[str, ...]
    available_attributes: dict[str, Any]
    inherited_context: dict[str, Any]
    confidence_level_available: str
    traceability: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class StructureCatalogView:
    """Vista de solo lectura del catálogo de estructuras comparativas."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    structures: tuple[StructureView, ...]
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class ProviderOrganizationInputView:
    """Vista combinada de entrada para la organización de proveedores."""

    structure_catalog: StructureCatalogView
    column_catalog: ColumnCatalogView
    row_catalog: RowCatalogView


def _parse_row(item: dict[str, Any]) -> RowDefinitionView:
    column_refs_raw = item.get("column_references", [])
    column_refs = (
        tuple(str(ref) for ref in column_refs_raw)
        if isinstance(column_refs_raw, list)
        else ()
    )
    return RowDefinitionView(
        row_id=str(item["row_id"]),
        provider_id=str(item["provider_id"]),
        logical_position=int(item.get("logical_position", 0)),
        group_id=str(item.get("group_id", "")),
        table_id=str(item.get("table_id", "")),
        column_references=column_refs,
    )


def _parse_row_set(payload: dict[str, Any]) -> RowSetView:
    rows_raw = payload.get("rows", [])
    rows = tuple(_parse_row(item) for item in rows_raw) if isinstance(rows_raw, list) else ()
    return RowSetView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        rows=rows,
        source_structure_catalog_id=str(payload.get("source_structure_catalog_id", "")),
        source_column_catalog_id=str(payload.get("source_column_catalog_id", "")),
    )


def _parse_column_set(payload: dict[str, Any]) -> ColumnSetView:
    columns_raw = payload.get("columns", [])
    columns: list[ColumnDefinitionView] = []
    if isinstance(columns_raw, list):
        for item in columns_raw:
            columns.append(
                ColumnDefinitionView(
                    column_id=str(item["column_id"]),
                    attribute_name=str(item.get("attribute_name", "")),
                    group_id=str(item.get("group_id", payload.get("group_id", ""))),
                    table_id=str(item.get("table_id", payload.get("table_id", ""))),
                ),
            )
    return ColumnSetView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        columns=tuple(columns),
    )


def _parse_structure(payload: dict[str, Any]) -> StructureView:
    metadata_prepared = dict(payload.get("metadata_prepared", {}))
    domain_reference = dict(payload.get("domain_reference", {}))
    providers_raw = metadata_prepared.get("available_providers", [])
    providers = tuple(str(provider) for provider in providers_raw) if isinstance(providers_raw, list) else ()
    available_attributes = dict(metadata_prepared.get("available_attributes", {}))
    inherited_context = dict(metadata_prepared.get("inherited_context", {}))

    return StructureView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        document_id=str(domain_reference.get("document_id", "")),
        comparative_model_id=str(domain_reference.get("comparative_model_id", "")),
        available_providers=providers,
        available_attributes=available_attributes,
        inherited_context=inherited_context,
        confidence_level_available=str(
            metadata_prepared.get("confidence_level_available", "not_evaluated"),
        ),
        traceability=dict(payload.get("traceability", {})),
        metadata=dict(payload.get("metadata", {})),
    )


class ProviderOrganizationInputGateway:
    """
    Gateway de consumo de catálogos para el POE.

    Valida preparación para organización sin acceder a documentos originales.
    """

    STRUCTURE_REQUIRED: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "structures",
    )
    COLUMN_REQUIRED: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "column_sets",
    )
    ROW_REQUIRED: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "row_sets",
    )

    def validate(
        self,
        structure_catalog: dict[str, Any],
        column_catalog: dict[str, Any],
        row_catalog: dict[str, Any],
    ) -> ProviderOrganizationInputView:
        structure_view = self._validate_structure_catalog(structure_catalog)
        column_view = self._validate_column_catalog(column_catalog)
        row_view = self._validate_row_catalog(row_catalog)
        self._validate_catalog_consistency(structure_view, column_view, row_view)
        return ProviderOrganizationInputView(
            structure_catalog=structure_view,
            column_catalog=column_view,
            row_catalog=row_view,
        )

    def _validate_structure_catalog(self, catalog_dict: dict[str, Any]) -> StructureCatalogView:
        if not isinstance(catalog_dict, dict):
            raise StructureCatalogAccessError(
                "El catálogo de estructuras debe ser un diccionario",
            )
        missing = [field for field in self.STRUCTURE_REQUIRED if field not in catalog_dict]
        if missing:
            raise StructureCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de estructuras: " + ", ".join(missing),
            )
        structures_raw = catalog_dict.get("structures", [])
        if not isinstance(structures_raw, list):
            raise StructureCatalogAccessError("structures debe ser una lista")
        structures = tuple(_parse_structure(item) for item in structures_raw)
        return StructureCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            structures=structures,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_column_catalog(self, catalog_dict: dict[str, Any]) -> ColumnCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ColumnCatalogAccessError(
                "El catálogo de columnas debe ser un diccionario",
            )
        missing = [field for field in self.COLUMN_REQUIRED if field not in catalog_dict]
        if missing:
            raise ColumnCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de columnas: " + ", ".join(missing),
            )
        column_sets_raw = catalog_dict.get("column_sets", [])
        if not isinstance(column_sets_raw, list):
            raise ColumnCatalogAccessError("column_sets debe ser una lista")
        column_sets = tuple(_parse_column_set(item) for item in column_sets_raw)
        return ColumnCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_structure_catalog_id=str(catalog_dict.get("source_structure_catalog_id", "")),
            column_sets=column_sets,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_row_catalog(self, catalog_dict: dict[str, Any]) -> RowCatalogView:
        if not isinstance(catalog_dict, dict):
            raise RowCatalogAccessError(
                "El catálogo de filas debe ser un diccionario",
            )
        missing = [field for field in self.ROW_REQUIRED if field not in catalog_dict]
        if missing:
            raise RowCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de filas: " + ", ".join(missing),
            )
        if not bool(catalog_dict.get("provider_organization_engine_prepared", True)):
            raise RowCatalogAccessError(
                "El catálogo de filas no está preparado para organización de proveedores",
            )
        row_sets_raw = catalog_dict.get("row_sets", [])
        if not isinstance(row_sets_raw, list):
            raise RowCatalogAccessError("row_sets debe ser una lista")
        row_sets = tuple(_parse_row_set(item) for item in row_sets_raw)
        return RowCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_structure_catalog_id=str(catalog_dict.get("source_structure_catalog_id", "")),
            source_column_catalog_id=str(catalog_dict.get("source_column_catalog_id", "")),
            row_sets=row_sets,
            provider_organization_engine_prepared=True,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_catalog_consistency(
        self,
        structure_view: StructureCatalogView,
        column_view: ColumnCatalogView,
        row_view: RowCatalogView,
    ) -> None:
        if not (
            structure_view.process_id == column_view.process_id == row_view.process_id
        ):
            raise StructureCatalogAccessError(
                "Los process_id de los catálogos no coinciden",
            )
        if not (structure_view.model_id == column_view.model_id == row_view.model_id):
            raise StructureCatalogAccessError(
                "Los model_id de los catálogos no coinciden",
            )
        if (
            column_view.source_structure_catalog_id
            and structure_view.catalog_id
            and column_view.source_structure_catalog_id != structure_view.catalog_id
        ):
            raise ColumnCatalogAccessError(
                "El source_structure_catalog_id no coincide con el catálogo de estructuras",
            )
        if (
            row_view.source_column_catalog_id
            and column_view.catalog_id
            and row_view.source_column_catalog_id != column_view.catalog_id
        ):
            raise RowCatalogAccessError(
                "El source_column_catalog_id no coincide con el catálogo de columnas",
            )
        if (
            row_view.source_structure_catalog_id
            and structure_view.catalog_id
            and row_view.source_structure_catalog_id != structure_view.catalog_id
        ):
            raise RowCatalogAccessError(
                "El source_structure_catalog_id no coincide con el catálogo de estructuras",
            )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_structure_catalog": False,
            "modifies_column_catalog": False,
            "modifies_row_catalog": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "structure_required_fields": list(self.STRUCTURE_REQUIRED),
            "column_required_fields": list(self.COLUMN_REQUIRED),
            "row_required_fields": list(self.ROW_REQUIRED),
        }
