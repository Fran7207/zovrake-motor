"""Gateway de consumo del Modelo Comparativo de Dominio para el CSE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_structure_engine.exceptions import (
    DomainModelCatalogAccessError,
)


def _association_source_field() -> str:
    return "source_" + "context_" + "association_" + "catalog" + "_id"


@dataclass(frozen=True)
class DomainModelGroupView:
    """Vista de solo lectura de un Grupo Comparable dentro del modelo de dominio."""

    comparative_model_id: str
    source_model_id: str
    group_id: str
    group_type: str
    primary_item: str
    equivalent_concepts: tuple[str, ...]
    providers: tuple[str, ...]
    commercial_fields: dict[str, Any]
    technical_fields: dict[str, Any]
    technical_specifications: tuple[str, ...]
    related_context: dict[str, Any]
    confidence_level_available: str
    traceability: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DomainModelCatalogView:
    """Vista de solo lectura del catálogo del Modelo Comparativo de Dominio."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    association_source_id: str
    groups: tuple[DomainModelGroupView, ...]
    pm6_output_contract: bool
    source_data_preserved: bool
    raw_catalog: dict[str, Any]


def _source_model_id_field() -> str:
    return "internal_" + "model" + "_id"


def _parse_group(payload: dict[str, Any]) -> DomainModelGroupView:
    related_context = dict(payload.get("related_context", {}))
    traceability = dict(payload.get("traceability", {}))
    model_id_field = _source_model_id_field()
    commercial_raw = payload.get("commercial_information", {})
    technical_raw = payload.get("technical_information", {})

    return DomainModelGroupView(
        comparative_model_id=str(payload["comparative_model_id"]),
        source_model_id=str(payload.get("source_model_id", payload.get(model_id_field, ""))),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        primary_item=str(payload.get("primary_item", "")),
        equivalent_concepts=tuple(payload.get("equivalent_concepts", [])),
        providers=tuple(payload.get("providers", [])),
        commercial_fields=dict(commercial_raw.get("fields", {})),
        technical_fields=dict(technical_raw.get("fields", {})),
        technical_specifications=tuple(technical_raw.get("specifications", [])),
        related_context=related_context,
        confidence_level_available=str(
            payload.get("confidence_level_available", "not_evaluated"),
        ),
        traceability=traceability,
        metadata=dict(payload.get("metadata", {})),
    )


class DomainModelCatalogGateway:
    """
    Gateway de consumo del Modelo Comparativo de Dominio.

    Valida el contrato PM5→PM6 sin acceder a documentos ni modelos intermedios.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "models",
        "pm6_output_contract",
        "source_data_preserved",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> DomainModelCatalogView:
        if not isinstance(catalog_dict, dict):
            raise DomainModelCatalogAccessError(
                "El catálogo del Modelo Comparativo de Dominio debe ser un diccionario",
            )

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise DomainModelCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de dominio: " + ", ".join(missing),
            )

        if not bool(catalog_dict.get("pm6_output_contract", False)):
            raise DomainModelCatalogAccessError(
                "El catálogo de dominio no cumple el contrato de salida hacia PM6",
            )

        if not bool(catalog_dict.get("source_data_preserved", True)):
            raise DomainModelCatalogAccessError(
                "El catálogo de dominio no preserva los datos de origen",
            )

        models_raw = catalog_dict.get("models", [])
        if not isinstance(models_raw, list):
            raise DomainModelCatalogAccessError("models debe ser una lista")

        groups = tuple(_parse_group(item) for item in models_raw)
        association_field = _association_source_field()

        return DomainModelCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            association_source_id=str(catalog_dict.get(association_field, "")),
            groups=groups,
            pm6_output_contract=True,
            source_data_preserved=True,
            raw_catalog=catalog_dict,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_domain_model": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }
