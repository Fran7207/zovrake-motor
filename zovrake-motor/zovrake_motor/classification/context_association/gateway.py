"""Gateway de consumo del catálogo de grupos comparables y contexto integrado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.context_association.exceptions import (
    ComparableGroupCatalogAccessError,
    IntegratedContextAccessError,
)
from zovrake_motor.classification.context_association.models import PreservedIntegratedContext


@dataclass(frozen=True)
class ComparableGroupCatalogView:
    """Vista de solo lectura del catálogo de grupos comparables."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    groups: tuple[dict[str, Any], ...]
    raw_catalog: dict[str, Any]


@dataclass(frozen=True)
class ContextAssociationInputView:
    """Vista de entrada validada para asociación de contexto."""

    group_catalog: ComparableGroupCatalogView
    preserved_context: PreservedIntegratedContext
    raw_context: dict[str, Any]


def _parse_preserved_context(payload: dict[str, Any], *, process_id: UUID) -> PreservedIntegratedContext:
    description = payload.get("description")
    if description is None and "detalles_requerimiento" in payload:
        description = payload["detalles_requerimiento"]
    if description is None:
        raise IntegratedContextAccessError(
            "El contexto integrado debe incluir 'description' (Detalles del requerimiento)",
        )

    context_process_id = payload.get("process_id", str(process_id))
    return PreservedIntegratedContext(
        context_id=str(payload.get("context_id", f"ctx://{process_id}")),
        description=str(description),
        process_id=UUID(str(context_process_id)),
        codigo_req=str(payload.get("codigo_req", "")),
        observations=tuple(payload.get("observations", [])),
        priorities=tuple(payload.get("priorities", [])),
        restrictions=tuple(payload.get("restrictions", [])),
        additional_notes=tuple(payload.get("additional_notes", [])),
        metadata=dict(payload.get("metadata", {})),
        immutable=bool(payload.get("immutable", True)),
    )


class ContextAssociationGateway:
    """
    Gateway de consumo para el CAE-Context.

    Valida catálogo de grupos y contexto sin acceder al documento original.
    """

    GROUP_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "groups",
    )

    CONTEXT_REQUIRED_FIELDS: tuple[str, ...] = ("description",)

    def validate(
        self,
        comparable_group_catalog: dict[str, Any],
        integrated_context: dict[str, Any],
        *,
        process_id: UUID,
    ) -> ContextAssociationInputView:
        group_view = self._validate_group_catalog(comparable_group_catalog)
        preserved_context = self._validate_integrated_context(integrated_context, process_id=process_id)
        return ContextAssociationInputView(
            group_catalog=group_view,
            preserved_context=preserved_context,
            raw_context=integrated_context,
        )

    def _validate_group_catalog(self, catalog_dict: dict[str, Any]) -> ComparableGroupCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ComparableGroupCatalogAccessError(
                "El catálogo de grupos comparables debe ser un diccionario",
            )

        missing = [field for field in self.GROUP_CATALOG_REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ComparableGroupCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo de grupos: {', '.join(missing)}",
            )

        if not bool(catalog_dict.get("context_association_prepared", True)):
            raise ComparableGroupCatalogAccessError(
                "El catálogo de grupos comparables no está preparado para asociación de contexto",
            )

        groups_raw = catalog_dict.get("groups", [])
        if not isinstance(groups_raw, list):
            raise ComparableGroupCatalogAccessError("groups debe ser una lista")

        return ComparableGroupCatalogView(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            groups=tuple(dict(group) for group in groups_raw),
            raw_catalog=catalog_dict,
        )

    def _validate_integrated_context(
        self,
        context_dict: dict[str, Any],
        *,
        process_id: UUID,
    ) -> PreservedIntegratedContext:
        if not isinstance(context_dict, dict):
            raise IntegratedContextAccessError("El contexto integrado debe ser un diccionario")

        has_description = "description" in context_dict or "detalles_requerimiento" in context_dict
        if not has_description:
            raise IntegratedContextAccessError(
                "El contexto integrado debe incluir 'description' (Detalles del requerimiento)",
            )

        return _parse_preserved_context(context_dict, process_id=process_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_comparable_group_catalog": False,
            "modifies_integrated_context": False,
            "accesses_original_documents": False,
            "group_catalog_required_fields": list(self.GROUP_CATALOG_REQUIRED_FIELDS),
            "context_required_fields": list(self.CONTEXT_REQUIRED_FIELDS),
        }
