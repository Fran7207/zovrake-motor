"""Gateway de consumo de catálogos del CSE y el DCB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.dynamic_row_builder.exceptions import (
    ColumnCatalogAccessError,
    StructureCatalogAccessError,
)


@dataclass(frozen=True)
class ColumnDefinitionView:
    """Vista de solo lectura de una columna dinámica."""

    column_id: str
    attribute_name: str
    logical_position: int
    group_id: str
    table_id: str


@dataclass(frozen=True)
class ColumnSetView:
    """Vista de solo lectura de un conjunto de columnas."""

    table_id: str
    group_id: str
    columns: tuple[ColumnDefinitionView, ...]
    source_structure_catalog_id: str


@dataclass(frozen=True)
class ColumnCatalogView:
    """Vista de solo lectura del catálogo de columnas dinámicas."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    column_sets: tuple[ColumnSetView, ...]
    dynamic_row_builder_prepared: bool
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class StructureView:
    """Vista de solo lectura de una estructura base del CSE."""

    table_id: str
    group_id: str
    available_providers: tuple[str, ...]
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
class RowBuildInputView:
    """Vista combinada de entrada para la construcción de filas."""

    column_catalog: ColumnCatalogView
    structure_catalog: StructureCatalogView


def _parse_column_set(payload: dict[str, Any]) -> ColumnSetView:
    columns_raw = payload.get("columns", [])
    columns: list[ColumnDefinitionView] = []
    if isinstance(columns_raw, list):
        for item in columns_raw:
            columns.append(
                ColumnDefinitionView(
                    column_id=str(item["column_id"]),
                    attribute_name=str(item.get("attribute_name", "")),
                    logical_position=int(item.get("logical_position", 0)),
                    group_id=str(item.get("group_id", payload.get("group_id", ""))),
                    table_id=str(item.get("table_id", payload.get("table_id", ""))),
                ),
            )
    return ColumnSetView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        columns=tuple(columns),
        source_structure_catalog_id=str(payload.get("source_structure_catalog_id", "")),
    )


def _parse_structure(payload: dict[str, Any]) -> StructureView:
    metadata_prepared = dict(payload.get("metadata_prepared", {}))
    providers_raw = metadata_prepared.get("available_providers", [])
    providers = tuple(str(provider) for provider in providers_raw) if isinstance(providers_raw, list) else ()

    return StructureView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        available_providers=providers,
        traceability=dict(payload.get("traceability", {})),
        metadata=dict(payload.get("metadata", {})),
    )


class RowBuildInputGateway:
    """
    Gateway de consumo de catálogos para el DRB.

    Valida preparación para filas sin acceder a documentos originales.
    """

    COLUMN_REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "column_sets",
    )

    STRUCTURE_REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "structures",
    )

    def validate(
        self,
        column_catalog: dict[str, Any],
        structure_catalog: dict[str, Any],
    ) -> RowBuildInputView:
        column_view = self._validate_column_catalog(column_catalog)
        structure_view = self._validate_structure_catalog(structure_catalog)
        self._validate_catalog_consistency(column_view, structure_view)
        return RowBuildInputView(
            column_catalog=column_view,
            structure_catalog=structure_view,
        )

    def _validate_column_catalog(self, catalog_dict: dict[str, Any]) -> ColumnCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ColumnCatalogAccessError(
                "El catálogo de columnas debe ser un diccionario",
            )

        missing = [field for field in self.COLUMN_REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ColumnCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de columnas: " + ", ".join(missing),
            )

        if not bool(catalog_dict.get("dynamic_row_builder_prepared", True)):
            raise ColumnCatalogAccessError(
                "El catálogo de columnas no está preparado para construcción de filas",
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
            dynamic_row_builder_prepared=True,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_structure_catalog(self, catalog_dict: dict[str, Any]) -> StructureCatalogView:
        if not isinstance(catalog_dict, dict):
            raise StructureCatalogAccessError(
                "El catálogo de estructuras debe ser un diccionario",
            )

        missing = [field for field in self.STRUCTURE_REQUIRED_FIELDS if field not in catalog_dict]
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

    def _validate_catalog_consistency(
        self,
        column_view: ColumnCatalogView,
        structure_view: StructureCatalogView,
    ) -> None:
        if column_view.process_id != structure_view.process_id:
            raise ColumnCatalogAccessError(
                "El process_id del catálogo de columnas no coincide con el de estructuras",
            )
        if column_view.model_id != structure_view.model_id:
            raise ColumnCatalogAccessError(
                "El model_id del catálogo de columnas no coincide con el de estructuras",
            )
        if (
            column_view.source_structure_catalog_id
            and structure_view.catalog_id
            and column_view.source_structure_catalog_id != structure_view.catalog_id
        ):
            raise ColumnCatalogAccessError(
                "El source_structure_catalog_id no coincide con el catálogo de estructuras",
            )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_column_catalog": False,
            "modifies_structure_catalog": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "column_required_fields": list(self.COLUMN_REQUIRED_FIELDS),
            "structure_required_fields": list(self.STRUCTURE_REQUIRED_FIELDS),
        }
