"""Utilidades de construcción de asociaciones de contexto."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.classification.context_association.gateway import ContextAssociationInputView
from zovrake_motor.classification.context_association.models import (
    ContextAssociationCatalog,
    ContextAssociationRecord,
    ContextAssociationTraceability,
    PreservedIntegratedContext,
)
from zovrake_motor.config.categories.classification import ContextAssociationSettings


def build_association_id(model_id: str, sequence: int) -> str:
    return f"cae://{model_id}/association-{sequence:04d}"


def build_context_association_record(
    *,
    input_view: ContextAssociationInputView,
    group: dict[str, Any],
    preserved_context: PreservedIntegratedContext,
    association_id: str,
    settings: ContextAssociationSettings,
) -> ContextAssociationRecord:
    traceability_raw = group.get("traceability", {})
    return ContextAssociationRecord(
        association_id=association_id,
        group_id=str(group["group_id"]),
        internal_group_id=str(group["internal_group_id"]),
        context_id=preserved_context.context_id,
        traceability=ContextAssociationTraceability(
            process_id=input_view.group_catalog.process_id,
            document_id=input_view.group_catalog.document_id,
            model_id=input_view.group_catalog.model_id,
            source_comparable_group_catalog_id=input_view.group_catalog.catalog_id,
            group_id=str(group["group_id"]),
            internal_group_id=str(group["internal_group_id"]),
            context_id=preserved_context.context_id,
            equivalence_ids=tuple(traceability_raw.get("equivalence_ids", [])),
            concept_ids=tuple(traceability_raw.get("concept_ids", [])),
            normalized_concept_ids=tuple(traceability_raw.get("normalized_concept_ids", [])),
            document_reference=str(traceability_raw.get("document_reference", "")),
            canonical_reference=str(traceability_raw.get("canonical_reference", "")),
            original_preserved=bool(traceability_raw.get("original_preserved", True)),
            context_preserved=True,
        ),
        metadata={
            "associator_strategy": "uniform_group_context",
            "context_immutable": settings.preserve_context_immutability,
            "group_unmodified": True,
        },
    )


def build_context_association_catalog(
    *,
    input_view: ContextAssociationInputView,
    associations: tuple[ContextAssociationRecord, ...],
    preserved_context: PreservedIntegratedContext,
    comparative_domain_model_prepared: bool,
) -> ContextAssociationCatalog:
    return ContextAssociationCatalog(
        catalog_id=f"cae-catalog://{input_view.group_catalog.model_id}",
        process_id=input_view.group_catalog.process_id,
        model_id=input_view.group_catalog.model_id,
        document_id=input_view.group_catalog.document_id,
        source_comparable_group_catalog_id=input_view.group_catalog.catalog_id,
        preserved_context=preserved_context,
        preserved_groups=input_view.group_catalog.groups,
        associations=associations,
        comparable_group_catalog_preserved=True,
        context_preserved=True,
        comparative_domain_model_prepared=comparative_domain_model_prepared,
    )
