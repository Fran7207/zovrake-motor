"""Gateway de consumo de catálogos del CSE, DCB, DRB, POE, GIE y TME."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_model_builder.exceptions import (
    ColumnCatalogAccessError,
    EnrichedCatalogAccessError,
    IntegrityReportAccessError,
    ProviderCatalogAccessError,
    RowCatalogAccessError,
    StructureCatalogAccessError,
)


@dataclass(frozen=True)
class EnrichedTableView:
    enrichment_id: str
    table_id: str
    group_id: str
    group_type: str
    inherited_context: dict[str, Any]
    confidence_level_available: str
    traceability: dict[str, Any]
    metadata: dict[str, Any]
    column_references: tuple[str, ...]
    row_references: tuple[str, ...]
    provider_references: tuple[str, ...]


@dataclass(frozen=True)
class EnrichedCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    enriched_tables: tuple[EnrichedTableView, ...]
    comparative_model_builder_prepared: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class StructureView:
    table_id: str
    group_id: str
    group_type: str
    metadata_prepared: dict[str, Any]


@dataclass(frozen=True)
class StructureCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    structures: tuple[StructureView, ...]
    domain_model_preserved: bool


@dataclass(frozen=True)
class ColumnSetView:
    table_id: str
    group_id: str
    columns: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ColumnCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    column_sets: tuple[ColumnSetView, ...]


@dataclass(frozen=True)
class RowSetView:
    table_id: str
    group_id: str
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class RowCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    row_sets: tuple[RowSetView, ...]


@dataclass(frozen=True)
class ProviderSetView:
    table_id: str
    group_id: str
    providers: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ProviderCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    provider_sets: tuple[ProviderSetView, ...]


@dataclass(frozen=True)
class IntegrityCheckSetView:
    table_id: str
    is_valid: bool


@dataclass(frozen=True)
class IntegrityReportView:
    report_id: str
    process_id: UUID
    model_id: str
    check_sets: tuple[IntegrityCheckSetView, ...]


@dataclass(frozen=True)
class ModelBuildInputView:
    enriched_catalog: EnrichedCatalogView
    structure_catalog: StructureCatalogView
    column_catalog: ColumnCatalogView
    row_catalog: RowCatalogView
    provider_catalog: ProviderCatalogView
    integrity_report: IntegrityReportView


def _parse_enriched_table(payload: dict[str, Any]) -> EnrichedTableView:
    refs_cols = payload.get("column_references", [])
    refs_rows = payload.get("row_references", [])
    refs_prov = payload.get("provider_references", [])
    return EnrichedTableView(
        enrichment_id=str(payload["enrichment_id"]),
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        inherited_context=dict(payload.get("inherited_context", {})),
        confidence_level_available=str(
            payload.get("confidence_level_available", "not_evaluated"),
        ),
        traceability=dict(payload.get("traceability", {})),
        metadata=dict(payload.get("metadata", {})),
        column_references=tuple(str(ref) for ref in refs_cols) if isinstance(refs_cols, list) else (),
        row_references=tuple(str(ref) for ref in refs_rows) if isinstance(refs_rows, list) else (),
        provider_references=tuple(str(ref) for ref in refs_prov) if isinstance(refs_prov, list) else (),
    )


class ModelBuildInputGateway:
    """Gateway de consumo de catálogos para el CMB — solo lectura."""

    ENRICHED_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "document_id", "enriched_tables",
    )
    STRUCTURE_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "document_id", "structures",
    )
    COLUMN_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "column_sets",
    )
    ROW_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "row_sets",
    )
    PROVIDER_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "provider_sets",
    )
    INTEGRITY_REQUIRED: tuple[str, ...] = (
        "report_id", "process_id", "model_id", "check_sets",
    )

    def validate(
        self,
        enriched_catalog: dict[str, Any],
        structure_catalog: dict[str, Any],
        column_catalog: dict[str, Any],
        row_catalog: dict[str, Any],
        provider_catalog: dict[str, Any],
        integrity_report: dict[str, Any],
    ) -> ModelBuildInputView:
        enriched_view = self._validate_enriched(enriched_catalog)
        structure_view = self._validate_structure(structure_catalog)
        column_view = self._validate_column(column_catalog)
        row_view = self._validate_row(row_catalog)
        provider_view = self._validate_provider(provider_catalog)
        integrity_view = self._validate_integrity(integrity_report)
        self._validate_consistency(
            enriched_view,
            structure_view,
            column_view,
            row_view,
            provider_view,
            integrity_view,
        )
        return ModelBuildInputView(
            enriched_catalog=enriched_view,
            structure_catalog=structure_view,
            column_catalog=column_view,
            row_catalog=row_view,
            provider_catalog=provider_view,
            integrity_report=integrity_view,
        )

    def _validate_enriched(self, catalog_dict: dict[str, Any]) -> EnrichedCatalogView:
        if not isinstance(catalog_dict, dict):
            raise EnrichedCatalogAccessError(
                "El catálogo enriquecido debe ser un diccionario",
            )
        missing = [f for f in self.ENRICHED_REQUIRED if f not in catalog_dict]
        if missing:
            raise EnrichedCatalogAccessError(
                "Campos obligatorios ausentes en catálogo enriquecido: " + ", ".join(missing),
            )
        if not bool(catalog_dict.get("comparative_model_builder_prepared", True)):
            raise EnrichedCatalogAccessError(
                "El catálogo enriquecido no está preparado para construcción de modelos",
            )
        tables_raw = catalog_dict.get("enriched_tables", [])
        if not isinstance(tables_raw, list):
            raise EnrichedCatalogAccessError("enriched_tables debe ser una lista")
        tables = tuple(_parse_enriched_table(item) for item in tables_raw)
        return EnrichedCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            enriched_tables=tables,
            comparative_model_builder_prepared=True,
            raw_catalog=catalog_dict,
        )

    def _validate_structure(self, catalog_dict: dict[str, Any]) -> StructureCatalogView:
        if not isinstance(catalog_dict, dict):
            raise StructureCatalogAccessError("El catálogo de estructuras debe ser un diccionario")
        missing = [f for f in self.STRUCTURE_REQUIRED if f not in catalog_dict]
        if missing:
            raise StructureCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de estructuras: " + ", ".join(missing),
            )
        structures_raw = catalog_dict.get("structures", [])
        structures = tuple(
            StructureView(
                table_id=str(item["table_id"]),
                group_id=str(item["group_id"]),
                group_type=str(item.get("group_type", "")),
                metadata_prepared=dict(item.get("metadata_prepared", {})),
            )
            for item in structures_raw
            if isinstance(structures_raw, list)
        )
        return StructureCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            structures=structures,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
        )

    def _validate_column(self, catalog_dict: dict[str, Any]) -> ColumnCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ColumnCatalogAccessError("El catálogo de columnas debe ser un diccionario")
        missing = [f for f in self.COLUMN_REQUIRED if f not in catalog_dict]
        if missing:
            raise ColumnCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de columnas: " + ", ".join(missing),
            )
        column_sets = tuple(
            ColumnSetView(
                table_id=str(item["table_id"]),
                group_id=str(item["group_id"]),
                columns=tuple(item.get("columns", [])),
            )
            for item in catalog_dict.get("column_sets", [])
            if isinstance(catalog_dict.get("column_sets"), list)
        )
        return ColumnCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            column_sets=column_sets,
        )

    def _validate_row(self, catalog_dict: dict[str, Any]) -> RowCatalogView:
        if not isinstance(catalog_dict, dict):
            raise RowCatalogAccessError("El catálogo de filas debe ser un diccionario")
        missing = [f for f in self.ROW_REQUIRED if f not in catalog_dict]
        if missing:
            raise RowCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de filas: " + ", ".join(missing),
            )
        row_sets = tuple(
            RowSetView(
                table_id=str(item["table_id"]),
                group_id=str(item["group_id"]),
                rows=tuple(item.get("rows", [])),
            )
            for item in catalog_dict.get("row_sets", [])
            if isinstance(catalog_dict.get("row_sets"), list)
        )
        return RowCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            row_sets=row_sets,
        )

    def _validate_provider(self, catalog_dict: dict[str, Any]) -> ProviderCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ProviderCatalogAccessError(
                "El catálogo de proveedores debe ser un diccionario",
            )
        missing = [f for f in self.PROVIDER_REQUIRED if f not in catalog_dict]
        if missing:
            raise ProviderCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de proveedores: " + ", ".join(missing),
            )
        provider_sets = tuple(
            ProviderSetView(
                table_id=str(item["table_id"]),
                group_id=str(item["group_id"]),
                providers=tuple(item.get("providers", [])),
            )
            for item in catalog_dict.get("provider_sets", [])
            if isinstance(catalog_dict.get("provider_sets"), list)
        )
        return ProviderCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            provider_sets=provider_sets,
        )

    def _validate_integrity(self, report_dict: dict[str, Any]) -> IntegrityReportView:
        if not isinstance(report_dict, dict):
            raise IntegrityReportAccessError(
                "El reporte de integridad debe ser un diccionario",
            )
        missing = [f for f in self.INTEGRITY_REQUIRED if f not in report_dict]
        if missing:
            raise IntegrityReportAccessError(
                "Campos obligatorios ausentes en reporte de integridad: " + ", ".join(missing),
            )
        check_sets = tuple(
            IntegrityCheckSetView(
                table_id=str(item.get("table_id", "")),
                is_valid=bool(item.get("is_valid", True)),
            )
            for item in report_dict.get("check_sets", [])
            if isinstance(report_dict.get("check_sets"), list)
        )
        return IntegrityReportView(
            report_id=str(report_dict["report_id"]),
            process_id=UUID(str(report_dict["process_id"])),
            model_id=str(report_dict["model_id"]),
            check_sets=check_sets,
        )

    def _validate_consistency(
        self,
        enriched_view: EnrichedCatalogView,
        structure_view: StructureCatalogView,
        column_view: ColumnCatalogView,
        row_view: RowCatalogView,
        provider_view: ProviderCatalogView,
        integrity_view: IntegrityReportView,
    ) -> None:
        process_ids = {
            enriched_view.process_id,
            structure_view.process_id,
            column_view.process_id,
            row_view.process_id,
            provider_view.process_id,
            integrity_view.process_id,
        }
        if len(process_ids) != 1:
            raise EnrichedCatalogAccessError("Los process_id de los catálogos no coinciden")
        model_ids = {
            enriched_view.model_id,
            structure_view.model_id,
            column_view.model_id,
            row_view.model_id,
            provider_view.model_id,
            integrity_view.model_id,
        }
        if len(model_ids) != 1:
            raise EnrichedCatalogAccessError("Los model_id de los catálogos no coinciden")

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_catalogs": False,
            "accesses_source_files": False,
        }
