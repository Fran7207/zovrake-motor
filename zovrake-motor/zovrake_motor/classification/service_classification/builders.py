"""Utilidades de construcción de servicios y trazabilidad."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_analysis.enums import ConceptKind
from zovrake_motor.classification.concept_analysis.models import ConceptCandidate
from zovrake_motor.classification.service_classification.enums import ServiceClassificationStatus
from zovrake_motor.classification.service_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.service_classification.models import (
    ServiceCatalog,
    ServiceCommercialInformation,
    ServiceModelReference,
    ServiceRecord,
    ServiceTechnicalInformation,
    ServiceTraceability,
)


def build_service_id(model_id: str, sequence: int) -> str:
    return f"sce://{model_id}/service-{sequence:04d}"


def build_service_traceability(concept: ConceptCandidate) -> ServiceTraceability:
    traceability = concept.traceability
    location = concept.location
    return ServiceTraceability(
        process_id=traceability.process_id,
        document_id=traceability.document_id,
        model_id=traceability.model_id,
        concept_id=concept.concept_id,
        document_reference=traceability.document_reference,
        canonical_reference=location.canonical_reference,
        extraction_reference=location.extraction_reference,
        source_reference=location.source_reference,
        adapter_name=traceability.adapter_name,
        format_type=traceability.format_type,
        original_preserved=traceability.original_preserved,
    )


def _resolve_service_scope(concept: ConceptCandidate) -> str:
    metadata = concept.metadata
    if concept.kind == ConceptKind.COMMERCIAL_CONDITION:
        return str(metadata.get("condition_type", concept.location.field_name or "condicion_comercial"))
    if concept.kind == ConceptKind.OBSERVATION:
        return str(metadata.get("observation_type", concept.location.field_name or "observacion"))
    if concept.kind == ConceptKind.TECHNICAL_ELEMENT:
        return str(concept.location.field_name or "especificacion_tecnica")
    return str(metadata.get("service_scope", concept.location.section))


def build_service_from_concept(
    *,
    catalog_view: ConceptCatalogView,
    concept: ConceptCandidate,
    sequence: int,
) -> ServiceRecord:
    metadata = concept.metadata
    unit_price = str(metadata.get("unit_price", ""))
    quantity = str(metadata.get("quantity", ""))
    unit = str(metadata.get("unit", ""))
    specifications: tuple[str, ...] = ()

    if concept.kind == ConceptKind.TECHNICAL_ELEMENT:
        specifications = (concept.original_description,)

    return ServiceRecord(
        service_id=build_service_id(catalog_view.model_id, sequence),
        concept_id=concept.concept_id,
        original_name=concept.original_description,
        description=concept.original_description,
        service_scope=_resolve_service_scope(concept),
        unit=unit,
        quantity=quantity,
        commercial_information=ServiceCommercialInformation(
            unit_price=unit_price,
            currency=str(metadata.get("currency", "")),
            fields={
                key: value
                for key, value in metadata.items()
                if key in {"condition_type", "observation_type", "commercial_field"}
            },
        ),
        technical_information=ServiceTechnicalInformation(
            specifications=specifications,
            fields={
                key: value
                for key, value in metadata.items()
                if key.startswith("technical_")
            },
        ),
        model_reference=ServiceModelReference(
            model_id=catalog_view.model_id,
            document_id=catalog_view.document_id,
            concept_id=concept.concept_id,
        ),
        traceability=build_service_traceability(concept),
        concept_kind=concept.kind.value,
        status=ServiceClassificationStatus.CLASSIFIED,
        metadata=dict(metadata),
    )


def build_service_catalog(
    *,
    catalog_view: ConceptCatalogView,
    services: tuple[ServiceRecord, ...],
    normalization_prepared: bool,
    equivalence_detection_prepared: bool,
    comparable_group_builder_prepared: bool,
) -> ServiceCatalog:
    return ServiceCatalog(
        catalog_id=f"sce-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_concept_catalog_id=catalog_view.catalog_id,
        services=services,
        normalization_prepared=normalization_prepared,
        equivalence_detection_prepared=equivalence_detection_prepared,
        comparable_group_builder_prepared=comparable_group_builder_prepared,
    )
