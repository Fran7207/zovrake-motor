"""Gateway de consumo del catálogo de asociaciones de contexto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.comparative_domain_model.exceptions import (
    ContextAssociationCatalogAccessError,
)
from zovrake_motor.classification.context_association.models import (
    ContextAssociationRecord,
    PreservedIntegratedContext,
)


@dataclass(frozen=True)
class ContextAssociationCatalogView:
    """Vista de solo lectura del catálogo de asociaciones."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    document_ids: tuple[str, ...]
    source_comparable_group_catalog_id: str
    preserved_context: PreservedIntegratedContext
    preserved_groups: tuple[dict[str, Any], ...]
    associations: tuple[ContextAssociationRecord, ...]
    raw_catalog: dict[str, Any]


def _parse_association(payload: dict[str, Any]) -> ContextAssociationRecord:
    from zovrake_motor.classification.context_association.models import ContextAssociationTraceability

    traceability_raw = payload.get("traceability", {})
    return ContextAssociationRecord(
        association_id=str(payload["association_id"]),
        group_id=str(payload["group_id"]),
        internal_group_id=str(payload.get("internal_group_id", "")),
        context_id=str(payload.get("context_id", "")),
        traceability=ContextAssociationTraceability(
            process_id=UUID(str(traceability_raw["process_id"])),
            document_id=str(traceability_raw.get("document_id", "")),
            model_id=str(traceability_raw.get("model_id", "")),
            source_comparable_group_catalog_id=str(
                traceability_raw.get("source_comparable_group_catalog_id", ""),
            ),
            group_id=str(traceability_raw.get("group_id", "")),
            internal_group_id=str(traceability_raw.get("internal_group_id", "")),
            context_id=str(traceability_raw.get("context_id", "")),
            equivalence_ids=tuple(traceability_raw.get("equivalence_ids", [])),
            concept_ids=tuple(traceability_raw.get("concept_ids", [])),
            normalized_concept_ids=tuple(traceability_raw.get("normalized_concept_ids", [])),
            document_reference=str(traceability_raw.get("document_reference", "")),
            canonical_reference=str(traceability_raw.get("canonical_reference", "")),
            original_preserved=bool(traceability_raw.get("original_preserved", True)),
            context_preserved=bool(traceability_raw.get("context_preserved", True)),
            document_ids=tuple(traceability_raw.get("document_ids", [])),
        ),
        metadata=dict(payload.get("metadata", {})),
    )


def _parse_preserved_context(payload: dict[str, Any]) -> PreservedIntegratedContext:
    return PreservedIntegratedContext(
        context_id=str(payload["context_id"]),
        description=str(payload["description"]),
        process_id=UUID(str(payload["process_id"])),
        codigo_req=str(payload.get("codigo_req", "")),
        observations=tuple(payload.get("observations", [])),
        priorities=tuple(payload.get("priorities", [])),
        restrictions=tuple(payload.get("restrictions", [])),
        additional_notes=tuple(payload.get("additional_notes", [])),
        metadata=dict(payload.get("metadata", {})),
        immutable=bool(payload.get("immutable", True)),
    )


class ContextAssociationCatalogGateway:
    """
    Gateway de consumo del catálogo de asociaciones para el CDMB.

    Valida preparación sin acceder al documento original.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "preserved_context",
        "preserved_groups",
        "associations",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> ContextAssociationCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ContextAssociationCatalogAccessError(
                "El catálogo de asociaciones debe ser un diccionario",
            )

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ContextAssociationCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo de asociaciones: {', '.join(missing)}",
            )

        if not bool(catalog_dict.get("comparative_domain_model_prepared", True)):
            raise ContextAssociationCatalogAccessError(
                "El catálogo de asociaciones no está preparado para construcción del modelo comparativo",
            )

        associations_raw = catalog_dict.get("associations", [])
        if not isinstance(associations_raw, list):
            raise ContextAssociationCatalogAccessError("associations debe ser una lista")

        groups_raw = catalog_dict.get("preserved_groups", [])
        if not isinstance(groups_raw, list):
            raise ContextAssociationCatalogAccessError("preserved_groups debe ser una lista")

        context_raw = catalog_dict.get("preserved_context", {})
        if not isinstance(context_raw, dict):
            raise ContextAssociationCatalogAccessError("preserved_context debe ser un diccionario")

        associations = tuple(_parse_association(item) for item in associations_raw)

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
                    for association in associations
                    for document_id in association.traceability.document_ids
                    if str(document_id)
                )
            )
        if not document_ids and catalog_dict.get("document_id"):
            document_ids = (str(catalog_dict["document_id"]),)

        return ContextAssociationCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            document_ids=document_ids,
            source_comparable_group_catalog_id=str(
                catalog_dict.get("source_comparable_group_catalog_id", ""),
            ),
            preserved_context=_parse_preserved_context(context_raw),
            preserved_groups=tuple(dict(group) for group in groups_raw),
            associations=associations,
            raw_catalog=catalog_dict,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_context_association_catalog": False,
            "accesses_original_documents": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }