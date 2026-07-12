"""Utilidades de construcción de materiales y trazabilidad."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_analysis.models import ConceptCandidate
from zovrake_motor.classification.material_classification.enums import MaterialClassificationStatus
from zovrake_motor.classification.material_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.material_classification.models import (
    MaterialCatalog,
    MaterialCommercialInformation,
    MaterialModelReference,
    MaterialRecord,
    MaterialTechnicalInformation,
    MaterialTraceability,
)


def build_material_id(model_id: str, sequence: int) -> str:
    return f"mce://{model_id}/material-{sequence:04d}"


def build_material_traceability(concept: ConceptCandidate) -> MaterialTraceability:
    traceability = concept.traceability
    location = concept.location
    return MaterialTraceability(
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


def build_material_from_concept(
    *,
    catalog_view: ConceptCatalogView,
    concept: ConceptCandidate,
    sequence: int,
) -> MaterialRecord:
    metadata = concept.metadata
    unit_price = str(metadata.get("unit_price", ""))
    quantity = str(metadata.get("quantity", ""))
    unit = str(metadata.get("unit", ""))

    return MaterialRecord(
        material_id=build_material_id(catalog_view.model_id, sequence),
        concept_id=concept.concept_id,
        original_name=concept.original_description,
        description=concept.original_description,
        unit=unit,
        quantity=quantity,
        commercial_information=MaterialCommercialInformation(
            unit_price=unit_price,
            currency=str(metadata.get("currency", "")),
            fields={
                key: value
                for key, value in metadata.items()
                if key in {"item_id", "unit_price", "quantity", "unit"}
            },
        ),
        technical_information=MaterialTechnicalInformation(
            specifications=tuple(
                str(metadata[key])
                for key in ("specifications", "technical_notes")
                if metadata.get(key)
            ),
            fields={
                key: value
                for key, value in metadata.items()
                if key.startswith("technical_")
            },
        ),
        model_reference=MaterialModelReference(
            model_id=catalog_view.model_id,
            document_id=catalog_view.document_id,
            concept_id=concept.concept_id,
        ),
        traceability=build_material_traceability(concept),
        concept_kind=concept.kind.value,
        status=MaterialClassificationStatus.CLASSIFIED,
        metadata=dict(metadata),
    )


def build_material_catalog(
    *,
    catalog_view: ConceptCatalogView,
    materials: tuple[MaterialRecord, ...],
    service_classification_prepared: bool,
    normalization_prepared: bool,
    equivalence_detection_prepared: bool,
    comparable_group_builder_prepared: bool,
) -> MaterialCatalog:
    return MaterialCatalog(
        catalog_id=f"mce-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_concept_catalog_id=catalog_view.catalog_id,
        materials=materials,
        service_classification_prepared=service_classification_prepared,
        normalization_prepared=normalization_prepared,
        equivalence_detection_prepared=equivalence_detection_prepared,
        comparable_group_builder_prepared=comparable_group_builder_prepared,
    )
