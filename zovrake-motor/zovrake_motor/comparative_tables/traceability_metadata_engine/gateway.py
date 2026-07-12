"""Gateway de consumo de catálogos del CSE, DCB, DRB, POE y GIE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.traceability_metadata_engine.exceptions import (
    ColumnCatalogAccessError,
    IntegrityReportAccessError,
    ProviderCatalogAccessError,
    RowCatalogAccessError,
    StructureCatalogAccessError,
)


@dataclass(frozen=True)
class ProviderView:
    organization_id: str
    provider_id: str
    group_id: str
    table_id: str
    row_id: str
    document_reference: str
    column_references: tuple[str, ...]
    inherited_context: dict[str, Any]
    confidence_level_available: str
    traceability: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ProviderSetView:
    table_id: str
    group_id: str
    providers: tuple[ProviderView, ...]


@dataclass(frozen=True)
class ProviderCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    provider_sets: tuple[ProviderSetView, ...]
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class RowView:
    row_id: str
    provider_id: str
    group_id: str
    table_id: str
    column_references: tuple[str, ...]
    traceability: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RowSetView:
    table_id: str
    group_id: str
    rows: tuple[RowView, ...]


@dataclass(frozen=True)
class RowCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    row_sets: tuple[RowSetView, ...]
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class ColumnView:
    column_id: str
    attribute_name: str
    group_id: str
    table_id: str
    traceability: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ColumnSetView:
    table_id: str
    group_id: str
    columns: tuple[ColumnView, ...]


@dataclass(frozen=True)
class ColumnCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    column_sets: tuple[ColumnSetView, ...]
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class StructureView:
    table_id: str
    internal_table_id: str
    group_id: str
    group_type: str
    document_id: str
    comparative_model_id: str
    domain_catalog_id: str
    inherited_context: dict[str, Any]
    confidence_level_available: str
    traceability: dict[str, Any]
    metadata: dict[str, Any]
    metadata_prepared: dict[str, Any]


@dataclass(frozen=True)
class StructureCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    structures: tuple[StructureView, ...]
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class IntegrityCheckSetView:
    table_id: str
    group_id: str
    is_valid: bool


@dataclass(frozen=True)
class IntegrityReportView:
    report_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_structure_catalog_id: str
    source_column_catalog_id: str
    source_row_catalog_id: str
    source_provider_catalog_id: str
    check_sets: tuple[IntegrityCheckSetView, ...]
    traceability_metadata_engine_prepared: bool
    domain_model_preserved: bool
    raw_report: dict[str, Any]


@dataclass(frozen=True)
class MetadataEnrichmentInputView:
    structure_catalog: StructureCatalogView
    column_catalog: ColumnCatalogView
    row_catalog: RowCatalogView
    provider_catalog: ProviderCatalogView
    integrity_report: IntegrityReportView


def _parse_provider(item: dict[str, Any]) -> ProviderView:
    refs_raw = item.get("column_references", [])
    refs = tuple(str(ref) for ref in refs_raw) if isinstance(refs_raw, list) else ()
    traceability = dict(item.get("traceability", {}))
    return ProviderView(
        organization_id=str(item.get("organization_id", "")),
        provider_id=str(item["provider_id"]),
        group_id=str(item.get("group_id", "")),
        table_id=str(item.get("table_id", "")),
        row_id=str(item.get("row_id", "")),
        document_reference=str(item.get("document_reference", "")),
        column_references=refs,
        inherited_context=dict(item.get("inherited_context", {})),
        confidence_level_available=str(
            item.get("confidence_level_available", "not_evaluated"),
        ),
        traceability=traceability,
        metadata=dict(item.get("metadata", {})),
    )


def _parse_provider_set(payload: dict[str, Any]) -> ProviderSetView:
    providers_raw = payload.get("providers", [])
    providers = (
        tuple(_parse_provider(item) for item in providers_raw)
        if isinstance(providers_raw, list)
        else ()
    )
    return ProviderSetView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        providers=providers,
    )


def _parse_row(item: dict[str, Any]) -> RowView:
    refs_raw = item.get("column_references", [])
    refs = tuple(str(ref) for ref in refs_raw) if isinstance(refs_raw, list) else ()
    return RowView(
        row_id=str(item["row_id"]),
        provider_id=str(item["provider_id"]),
        group_id=str(item.get("group_id", "")),
        table_id=str(item.get("table_id", "")),
        column_references=refs,
        traceability=dict(item.get("traceability", {})),
        metadata=dict(item.get("metadata", {})),
    )


def _parse_row_set(payload: dict[str, Any]) -> RowSetView:
    rows_raw = payload.get("rows", [])
    rows = tuple(_parse_row(item) for item in rows_raw) if isinstance(rows_raw, list) else ()
    return RowSetView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        rows=rows,
    )


def _parse_column(item: dict[str, Any], payload: dict[str, Any]) -> ColumnView:
    return ColumnView(
        column_id=str(item["column_id"]),
        attribute_name=str(item.get("attribute_name", "")),
        group_id=str(item.get("group_id", payload.get("group_id", ""))),
        table_id=str(item.get("table_id", payload.get("table_id", ""))),
        traceability=dict(item.get("traceability", {})),
        metadata=dict(item.get("metadata", {})),
    )


def _parse_column_set(payload: dict[str, Any]) -> ColumnSetView:
    columns_raw = payload.get("columns", [])
    columns: list[ColumnView] = []
    if isinstance(columns_raw, list):
        for item in columns_raw:
            columns.append(_parse_column(item, payload))
    return ColumnSetView(
        table_id=str(payload["table_id"]),
        group_id=str(payload["group_id"]),
        columns=tuple(columns),
    )


def _parse_structure(payload: dict[str, Any]) -> StructureView:
    domain_reference = dict(payload.get("domain_reference", {}))
    metadata_prepared = dict(payload.get("metadata_prepared", {}))
    traceability_raw = payload.get("traceability", {})
    traceability = dict(traceability_raw) if isinstance(traceability_raw, dict) else {}
    return StructureView(
        table_id=str(payload["table_id"]),
        internal_table_id=str(payload.get("internal_table_id", "")),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        document_id=str(domain_reference.get("document_id", "")),
        comparative_model_id=str(domain_reference.get("comparative_model_id", "")),
        domain_catalog_id=str(domain_reference.get("catalog_id", "")),
        inherited_context=dict(metadata_prepared.get("inherited_context", {})),
        confidence_level_available=str(
            metadata_prepared.get("confidence_level_available", "not_evaluated"),
        ),
        traceability=traceability,
        metadata=dict(payload.get("metadata", {})),
        metadata_prepared=metadata_prepared,
    )


def _parse_integrity_check_set(payload: dict[str, Any]) -> IntegrityCheckSetView:
    return IntegrityCheckSetView(
        table_id=str(payload.get("table_id", "")),
        group_id=str(payload.get("group_id", "")),
        is_valid=bool(payload.get("is_valid", True)),
    )


class MetadataEnrichmentInputGateway:
    """Gateway de consumo de catálogos para el TME — solo lectura."""

    STRUCTURE_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "document_id", "structures",
    )
    COLUMN_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "document_id", "column_sets",
    )
    ROW_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "document_id", "row_sets",
    )
    PROVIDER_REQUIRED: tuple[str, ...] = (
        "catalog_id", "process_id", "model_id", "document_id", "provider_sets",
    )
    INTEGRITY_REQUIRED: tuple[str, ...] = (
        "report_id", "process_id", "model_id", "document_id", "check_sets",
    )

    def validate(
        self,
        structure_catalog: dict[str, Any],
        column_catalog: dict[str, Any],
        row_catalog: dict[str, Any],
        provider_catalog: dict[str, Any],
        integrity_report: dict[str, Any],
    ) -> MetadataEnrichmentInputView:
        structure_view = self._validate_structure(structure_catalog)
        column_view = self._validate_column(column_catalog)
        row_view = self._validate_row(row_catalog)
        provider_view = self._validate_provider(provider_catalog)
        integrity_view = self._validate_integrity_report(integrity_report)
        self._validate_consistency(
            structure_view,
            column_view,
            row_view,
            provider_view,
            integrity_view,
        )
        return MetadataEnrichmentInputView(
            structure_catalog=structure_view,
            column_catalog=column_view,
            row_catalog=row_view,
            provider_catalog=provider_view,
            integrity_report=integrity_view,
        )

    def _validate_structure(self, catalog_dict: dict[str, Any]) -> StructureCatalogView:
        if not isinstance(catalog_dict, dict):
            raise StructureCatalogAccessError("El catálogo de estructuras debe ser un diccionario")
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

    def _validate_column(self, catalog_dict: dict[str, Any]) -> ColumnCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ColumnCatalogAccessError("El catálogo de columnas debe ser un diccionario")
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
            column_sets=column_sets,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_row(self, catalog_dict: dict[str, Any]) -> RowCatalogView:
        if not isinstance(catalog_dict, dict):
            raise RowCatalogAccessError("El catálogo de filas debe ser un diccionario")
        missing = [field for field in self.ROW_REQUIRED if field not in catalog_dict]
        if missing:
            raise RowCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de filas: " + ", ".join(missing),
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
            row_sets=row_sets,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_provider(self, catalog_dict: dict[str, Any]) -> ProviderCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ProviderCatalogAccessError(
                "El catálogo de proveedores debe ser un diccionario",
            )
        missing = [field for field in self.PROVIDER_REQUIRED if field not in catalog_dict]
        if missing:
            raise ProviderCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de proveedores: " + ", ".join(missing),
            )
        provider_sets_raw = catalog_dict.get("provider_sets", [])
        if not isinstance(provider_sets_raw, list):
            raise ProviderCatalogAccessError("provider_sets debe ser una lista")
        provider_sets = tuple(_parse_provider_set(item) for item in provider_sets_raw)
        return ProviderCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            provider_sets=provider_sets,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def _validate_integrity_report(self, report_dict: dict[str, Any]) -> IntegrityReportView:
        if not isinstance(report_dict, dict):
            raise IntegrityReportAccessError(
                "El reporte de integridad debe ser un diccionario",
            )
        missing = [field for field in self.INTEGRITY_REQUIRED if field not in report_dict]
        if missing:
            raise IntegrityReportAccessError(
                "Campos obligatorios ausentes en reporte de integridad: " + ", ".join(missing),
            )
        if not bool(report_dict.get("traceability_metadata_engine_prepared", True)):
            raise IntegrityReportAccessError(
                "El reporte de integridad no está preparado para enriquecimiento de metadatos",
            )
        check_sets_raw = report_dict.get("check_sets", [])
        if not isinstance(check_sets_raw, list):
            raise IntegrityReportAccessError("check_sets debe ser una lista")
        check_sets = tuple(_parse_integrity_check_set(item) for item in check_sets_raw)
        return IntegrityReportView(
            report_id=str(report_dict["report_id"]),
            process_id=UUID(str(report_dict["process_id"])),
            model_id=str(report_dict["model_id"]),
            document_id=str(report_dict["document_id"]),
            source_structure_catalog_id=str(report_dict.get("source_structure_catalog_id", "")),
            source_column_catalog_id=str(report_dict.get("source_column_catalog_id", "")),
            source_row_catalog_id=str(report_dict.get("source_row_catalog_id", "")),
            source_provider_catalog_id=str(report_dict.get("source_provider_catalog_id", "")),
            check_sets=check_sets,
            traceability_metadata_engine_prepared=True,
            domain_model_preserved=bool(report_dict.get("domain_model_preserved", True)),
            raw_report=report_dict,
        )

    def _validate_consistency(
        self,
        structure_view: StructureCatalogView,
        column_view: ColumnCatalogView,
        row_view: RowCatalogView,
        provider_view: ProviderCatalogView,
        integrity_view: IntegrityReportView,
    ) -> None:
        process_ids = {
            structure_view.process_id,
            column_view.process_id,
            row_view.process_id,
            provider_view.process_id,
            integrity_view.process_id,
        }
        if len(process_ids) != 1:
            raise StructureCatalogAccessError("Los process_id de los catálogos no coinciden")
        model_ids = {
            structure_view.model_id,
            column_view.model_id,
            row_view.model_id,
            provider_view.model_id,
            integrity_view.model_id,
        }
        if len(model_ids) != 1:
            raise StructureCatalogAccessError("Los model_id de los catálogos no coinciden")

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_catalogs": False,
            "modifies_integrity_report": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
        }
