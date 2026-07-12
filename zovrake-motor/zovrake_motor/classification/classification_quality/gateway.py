"""Gateway de consumo del catálogo del modelo comparativo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from .exceptions import (
    ComparativeDomainModelCatalogAccessError,
)


@dataclass(frozen=True)
class ComparativeDomainModelCatalogView:
    """Vista de solo lectura del catálogo del modelo comparativo."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_context_association_catalog_id: str
    models: tuple[dict[str, Any], ...]
    pm6_output_contract: bool
    source_data_preserved: bool
    raw_catalog: dict[str, Any]
    pipeline_snapshot: tuple[dict[str, Any], ...] = ()


class ComparativeDomainModelCatalogGateway:
    """
    Gateway de consumo para el CQF.

    Valida el catálogo sin acceder al documento original ni modificar datos.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "models",
    )

    def validate(
        self,
        catalog_dict: dict[str, Any],
        *,
        pipeline_snapshot: list[dict[str, Any]] | None = None,
    ) -> ComparativeDomainModelCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ComparativeDomainModelCatalogAccessError(
                "El catálogo del modelo comparativo debe ser un diccionario",
            )

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ComparativeDomainModelCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo del modelo comparativo: {', '.join(missing)}",
            )

        models_raw = catalog_dict.get("models", [])
        if not isinstance(models_raw, list):
            raise ComparativeDomainModelCatalogAccessError("models debe ser una lista")

        snapshot_tuple: tuple[dict[str, Any], ...] = ()
        if pipeline_snapshot is not None:
            if not isinstance(pipeline_snapshot, list):
                raise ComparativeDomainModelCatalogAccessError("pipeline_snapshot debe ser una lista")
            snapshot_tuple = tuple(dict(item) for item in pipeline_snapshot)

        return ComparativeDomainModelCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_context_association_catalog_id=str(
                catalog_dict.get("source_context_association_catalog_id", ""),
            ),
            models=tuple(dict(model) for model in models_raw),
            pm6_output_contract=bool(catalog_dict.get("pm6_output_contract", True)),
            source_data_preserved=bool(catalog_dict.get("source_data_preserved", True)),
            raw_catalog=catalog_dict,
            pipeline_snapshot=snapshot_tuple,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_comparative_domain_model_catalog": False,
            "accesses_original_documents": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }
