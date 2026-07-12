"""Gateway de consumo del catálogo de estructuras del CSE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.dynamic_column_builder.exceptions import (
    StructureCatalogAccessError,
)


@dataclass(frozen=True)
class StructureView:
    """Vista de solo lectura de una estructura base del CSE."""

    table_id: str
    internal_table_id: str
    group_id: str
    group_type: str
    comparative_model_id: str
    available_attributes: dict[str, Any]
    traceability: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class StructureCatalogView:
    """Vista de solo lectura del catálogo de estructuras comparativas."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_domain_catalog_id: str
    structures: tuple[StructureView, ...]
    dynamic_column_builder_prepared: bool
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


def _parse_structure(payload: dict[str, Any]) -> StructureView:
    domain_reference = dict(payload.get("domain_reference", {}))
    metadata_prepared = dict(payload.get("metadata_prepared", {}))
    available_attributes = dict(metadata_prepared.get("available_attributes", {}))

    return StructureView(
        table_id=str(payload["table_id"]),
        internal_table_id=str(payload.get("internal_table_id", "")),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        comparative_model_id=str(domain_reference.get("comparative_model_id", "")),
        available_attributes=available_attributes,
        traceability=dict(payload.get("traceability", {})),
        metadata=dict(payload.get("metadata", {})),
    )


class StructureCatalogGateway:
    """
    Gateway de consumo del catálogo de estructuras para el DCB.

    Valida preparación para columnas sin acceder a documentos originales.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "structures",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> StructureCatalogView:
        if not isinstance(catalog_dict, dict):
            raise StructureCatalogAccessError(
                "El catálogo de estructuras debe ser un diccionario",
            )

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise StructureCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de estructuras: " + ", ".join(missing),
            )

        if not bool(catalog_dict.get("dynamic_column_builder_prepared", True)):
            raise StructureCatalogAccessError(
                "El catálogo de estructuras no está preparado para construcción de columnas",
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
            source_domain_catalog_id=str(catalog_dict.get("source_domain_catalog_id", "")),
            structures=structures,
            dynamic_column_builder_prepared=True,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_structure_catalog": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }
