"""Gateway de consumo del Modelo Comparativo Definitivo para el EAE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.exceptions import (
    DefinitiveCatalogAccessError,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.governance import (
    PM7_DEFINITIVE_CATALOG_REQUIRED_FIELDS,
    PM7_DEFINITIVE_MODEL_REQUIRED_FIELDS,
)


@dataclass(frozen=True)
class DefinitiveComparativeModelView:
    """Vista de solo lectura de un Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    dynamic_columns: tuple[dict[str, Any], ...]
    dynamic_rows: tuple[dict[str, Any], ...]
    provider_organization: tuple[dict[str, Any], ...]
    commercial_information: dict[str, Any]
    technical_information: dict[str, Any]
    inherited_context: dict[str, Any]
    confidence_level_available: str
    metadata: dict[str, Any]
    traceability: dict[str, Any]
    motor_internal_references: dict[str, str]
    integrity_status: str
    source_data_preserved: bool


@dataclass(frozen=True)
class DefinitiveComparativeModelCatalogView:
    """Vista de solo lectura del catálogo definitivo PM6."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    document_ids: tuple[str, ...]
    models: tuple[DefinitiveComparativeModelView, ...]
    pm6_definitive_output_contract: bool
    pm7_input_contract_prepared: bool
    source_data_preserved: bool
    raw_catalog: dict[str, Any]


def _as_mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DefinitiveCatalogAccessError(f"{field_name} debe ser un diccionario")
    return dict(value)


def _parse_model(payload: dict[str, Any]) -> DefinitiveComparativeModelView:
    missing = [field for field in PM7_DEFINITIVE_MODEL_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise DefinitiveCatalogAccessError(
            "Campos obligatorios ausentes en modelo definitivo: " + ", ".join(missing),
        )

    return DefinitiveComparativeModelView(
        definitive_model_id=str(payload["definitive_model_id"]),
        comparative_table_id=str(payload["comparative_table_id"]),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        dynamic_columns=tuple(payload.get("dynamic_columns", [])),
        dynamic_rows=tuple(payload.get("dynamic_rows", [])),
        provider_organization=tuple(payload.get("provider_organization", [])),
        commercial_information=_as_mapping(
            payload.get("commercial_information", {}),
            field_name="commercial_information",
        ),
        technical_information=_as_mapping(
            payload.get("technical_information", {}),
            field_name="technical_information",
        ),
        inherited_context=_as_mapping(
            payload.get("inherited_context", {}),
            field_name="inherited_context",
        ),
        confidence_level_available=str(payload.get("confidence_level_available", "not_evaluated")),
        metadata=_as_mapping(payload.get("metadata", {}), field_name="metadata"),
        traceability=_as_mapping(payload.get("traceability", {}), field_name="traceability"),
        motor_internal_references={
            str(key): str(value)
            for key, value in dict(payload.get("motor_internal_references", {})).items()
        },
        integrity_status=str(payload.get("integrity_status", "unknown")),
        source_data_preserved=bool(payload.get("source_data_preserved", True)),
    )


class DefinitiveComparativeModelCatalogGateway:
    """
    Gateway de consumo del Modelo Comparativo Definitivo.

    Valida el contrato PM6→PM7 sin acceder a documentos ni modelos intermedios.
    """

    REQUIRED_FIELDS: tuple[str, ...] = PM7_DEFINITIVE_CATALOG_REQUIRED_FIELDS

    def validate(self, catalog_dict: dict[str, Any]) -> DefinitiveComparativeModelCatalogView:
        if not isinstance(catalog_dict, dict):
            raise DefinitiveCatalogAccessError(
                "El catálogo del Modelo Comparativo Definitivo debe ser un diccionario",
            )

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise DefinitiveCatalogAccessError(
                "Campos obligatorios ausentes en catálogo definitivo: " + ", ".join(missing),
            )

        if not bool(catalog_dict.get("pm6_definitive_output_contract", False)):
            raise DefinitiveCatalogAccessError(
                "El catálogo no cumple el contrato de salida PM6",
            )

        if not bool(catalog_dict.get("pm7_input_contract_prepared", False)):
            raise DefinitiveCatalogAccessError(
                "El catálogo no está preparado para consumo PM7",
            )

        if not bool(catalog_dict.get("source_data_preserved", True)):
            raise DefinitiveCatalogAccessError(
                "El catálogo definitivo no preserva los datos de origen",
            )

        models_raw = catalog_dict.get("models", [])
        if not isinstance(models_raw, list):
            raise DefinitiveCatalogAccessError("models debe ser una lista")

        models = tuple(_parse_model(item) for item in models_raw)

        document_ids = tuple(
            dict.fromkeys(
                str(document_id)
                for document_id in catalog_dict.get("document_ids", [])
                if str(document_id)
            )
        )
        if not document_ids:
            document_ids = tuple(
                dict.fromkeys(
                    str(document_id)
                    for model in models
                    for document_id in model.traceability.get("document_ids", [])
                    if str(document_id)
                )
            )
        if not document_ids and catalog_dict.get("document_id"):
            document_ids = (str(catalog_dict["document_id"]),)

        return DefinitiveComparativeModelCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            document_ids=document_ids,
            models=models,
            pm6_definitive_output_contract=True,
            pm7_input_contract_prepared=True,
            source_data_preserved=True,
            raw_catalog=catalog_dict,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_definitive_catalog": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "accesses_comparable_groups": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }