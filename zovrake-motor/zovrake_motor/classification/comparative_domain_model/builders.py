"""Utilidades de construcción del Modelo Comparativo de Dominio."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.comparative_domain_model.enums import ComparativeDomainModelBuildStatus
from zovrake_motor.classification.comparative_domain_model.gateway import ContextAssociationCatalogView
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainCommercialInformation,
    ComparativeDomainContextReference,
    ComparativeDomainModelCatalog,
    ComparativeDomainModelRecord,
    ComparativeDomainTechnicalInformation,
    ComparativeDomainTraceability,
)
from zovrake_motor.classification.context_association.models import (
    ContextAssociationRecord,
    PreservedIntegratedContext,
)
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings


def build_public_model_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_model_id(model_id: str, sequence: int) -> str:
    return f"cdmb://{model_id}/model-{sequence:04d}"


def _group_by_id(groups: tuple[dict[str, Any], ...]) -> dict[str, dict[str, Any]]:
    return {str(group["group_id"]): group for group in groups}


def _resolve_primary_item(group: dict[str, Any]) -> str:
    group_type = str(group.get("group_type", "material"))
    normalized_ids = group.get("normalized_concept_ids", [])
    if normalized_ids:
        return str(normalized_ids[0])
    return group_type


def build_comparative_domain_model_record(
    *,
    catalog_view: ContextAssociationCatalogView,
    association: ContextAssociationRecord,
    group: dict[str, Any],
    preserved_context: PreservedIntegratedContext,
    public_model_id: str,
    internal_sequence: int,
    settings: ComparativeDomainModelBuilderSettings,
) -> ComparativeDomainModelRecord:
    commercial_raw = group.get("commercial_information", {})
    technical_raw = group.get("technical_information", {})
    traceability_raw = group.get("traceability", {})

    return ComparativeDomainModelRecord(
        comparative_model_id=public_model_id,
        internal_model_id=build_internal_model_id(catalog_view.model_id, internal_sequence),
        group_id=str(group["group_id"]),
        group_type=str(group.get("group_type", "material")),
        primary_item=_resolve_primary_item(group),
        equivalent_concepts=tuple(group.get("normalized_concept_ids", [])),
        providers=tuple(group.get("provider_references", [])),
        commercial_information=ComparativeDomainCommercialInformation(
            fields=dict(commercial_raw.get("fields", {})),
        ),
        technical_information=ComparativeDomainTechnicalInformation(
            specifications=tuple(technical_raw.get("specifications", [])),
            fields=dict(technical_raw.get("fields", {})),
        ),
        related_context=ComparativeDomainContextReference(
            context_id=preserved_context.context_id,
            description=preserved_context.description,
            association_id=association.association_id,
            codigo_req=preserved_context.codigo_req,
        ),
        confidence_level_available=settings.default_confidence_level,
        traceability=ComparativeDomainTraceability(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            source_context_association_catalog_id=catalog_view.catalog_id,
            source_comparable_group_catalog_id=catalog_view.source_comparable_group_catalog_id,
            group_id=str(group["group_id"]),
            association_id=association.association_id,
            equivalence_ids=tuple(traceability_raw.get("equivalence_ids", [])),
            concept_ids=tuple(traceability_raw.get("concept_ids", [])),
            normalized_concept_ids=tuple(traceability_raw.get("normalized_concept_ids", [])),
            document_reference=str(traceability_raw.get("document_reference", "")),
            canonical_reference=str(traceability_raw.get("canonical_reference", "")),
            original_preserved=bool(traceability_raw.get("original_preserved", True)),
            context_preserved=True,
        ),
        status=ComparativeDomainModelBuildStatus.BUILT,
        metadata={
            "model_id_prefix": settings.model_id_prefix,
            "model_id_immutable": settings.model_id_immutable,
            "pm6_output_contract": settings.pm6_output_contract,
        },
    )


def build_comparative_domain_model_catalog(
    *,
    catalog_view: ContextAssociationCatalogView,
    models: tuple[ComparativeDomainModelRecord, ...],
    pm6_output_contract: bool,
) -> ComparativeDomainModelCatalog:
    return ComparativeDomainModelCatalog(
        catalog_id=f"cdmb-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_context_association_catalog_id=catalog_view.catalog_id,
        models=models,
        pm6_output_contract=pm6_output_contract,
        source_data_preserved=True,
    )
