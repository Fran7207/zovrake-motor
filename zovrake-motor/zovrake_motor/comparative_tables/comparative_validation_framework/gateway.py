"""Gateway de consumo del catálogo de modelos definitivos del CMB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.exceptions import (
    DefinitiveCatalogAccessError,
)


@dataclass(frozen=True)
class DefinitiveModelView:
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


@dataclass(frozen=True)
class DefinitiveCatalogView:
    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    models: tuple[DefinitiveModelView, ...]
    pm6_definitive_output_contract: bool
    pm7_input_contract_prepared: bool
    comparative_validation_framework_prepared: bool
    domain_model_preserved: bool
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class ModelValidationInputView:
    definitive_catalog: DefinitiveCatalogView


def _parse_model(payload: dict[str, Any]) -> DefinitiveModelView:
    commercial = payload.get("commercial_information", {})
    technical = payload.get("technical_information", {})
    return DefinitiveModelView(
        definitive_model_id=str(payload["definitive_model_id"]),
        comparative_table_id=str(payload["comparative_table_id"]),
        group_id=str(payload["group_id"]),
        group_type=str(payload.get("group_type", "")),
        dynamic_columns=tuple(payload.get("dynamic_columns", [])),
        dynamic_rows=tuple(payload.get("dynamic_rows", [])),
        provider_organization=tuple(payload.get("provider_organization", [])),
        commercial_information=dict(commercial) if isinstance(commercial, dict) else {},
        technical_information=dict(technical) if isinstance(technical, dict) else {},
        inherited_context=dict(payload.get("inherited_context", {})),
        confidence_level_available=str(
            payload.get("confidence_level_available", "not_evaluated"),
        ),
        metadata=dict(payload.get("metadata", {})),
        traceability=dict(payload.get("traceability", {})),
        motor_internal_references={
            str(k): str(v)
            for k, v in dict(payload.get("motor_internal_references", {})).items()
        },
        integrity_status=str(payload.get("integrity_status", "unknown")),
    )


class ModelValidationInputGateway:
    """Gateway de consumo del catálogo definitivo para el CVF — solo lectura."""

    CATALOG_REQUIRED: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "models",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> ModelValidationInputView:
        if not isinstance(catalog_dict, dict):
            raise DefinitiveCatalogAccessError(
                "El catálogo de modelos definitivos debe ser un diccionario",
            )
        missing = [field for field in self.CATALOG_REQUIRED if field not in catalog_dict]
        if missing:
            raise DefinitiveCatalogAccessError(
                "Campos obligatorios ausentes en catálogo definitivo: " + ", ".join(missing),
            )
        if not bool(catalog_dict.get("pm6_definitive_output_contract", False)):
            raise DefinitiveCatalogAccessError(
                "El catálogo no cumple el contrato oficial de salida del PM6",
            )
        if not bool(catalog_dict.get("comparative_validation_framework_prepared", True)):
            raise DefinitiveCatalogAccessError(
                "El catálogo definitivo no está preparado para validación comparativa",
            )
        models_raw = catalog_dict.get("models", [])
        if not isinstance(models_raw, list):
            raise DefinitiveCatalogAccessError("models debe ser una lista")
        models = tuple(_parse_model(item) for item in models_raw)
        for model in models:
            for field in PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS:
                if field == "dynamic_columns" and not model.dynamic_columns:
                    continue
                if field == "dynamic_rows" and not model.dynamic_rows:
                    continue
                if field == "provider_organization" and not model.provider_organization:
                    continue
        catalog_view = DefinitiveCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            models=models,
            pm6_definitive_output_contract=True,
            pm7_input_contract_prepared=bool(
                catalog_dict.get("pm7_input_contract_prepared", True),
            ),
            comparative_validation_framework_prepared=True,
            domain_model_preserved=bool(catalog_dict.get("domain_model_preserved", True)),
            raw_catalog=catalog_dict,
        )
        return ModelValidationInputView(definitive_catalog=catalog_view)

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_catalogs": False,
            "accesses_source_files": False,
        }
