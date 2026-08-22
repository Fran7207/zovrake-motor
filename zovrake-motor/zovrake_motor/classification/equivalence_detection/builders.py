"""Utilidades de construcción de equivalencias y trazabilidad."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_normalization.models import NormalizedConceptRecord
from zovrake_motor.classification.equivalence_detection.enums import (
    EquivalenceDetectionStatus,
    EquivalenceRelationType,
    EvidenceLevel,
)
from zovrake_motor.classification.equivalence_detection.gateway import NormalizedConceptCatalogView
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceCatalog,
    EquivalenceExplainability,
    EquivalenceRecord,
    EquivalenceTraceability,
)


def build_equivalence_id(model_id: str, sequence: int) -> str:
    return f"ede://{model_id}/equivalence-{sequence:04d}"


def build_equivalence_traceability(
    *,
    catalog_view: NormalizedConceptCatalogView,
    concepts: tuple[NormalizedConceptRecord, ...],
) -> EquivalenceTraceability:
    first = concepts[0]
    traceability = first.traceability

    document_ids = tuple(
        dict.fromkeys(
            concept.traceability.document_id
            for concept in concepts
            if concept.traceability.document_id
        )
    )

    return EquivalenceTraceability(
        process_id=traceability.process_id,
        document_id=traceability.document_id,
        document_ids=document_ids,
        model_id=traceability.model_id,
        source_normalized_catalog_id=catalog_view.catalog_id,
        concept_ids=tuple(concept.concept_id for concept in concepts),
        document_reference=traceability.document_reference,
        canonical_reference=traceability.canonical_reference,
        original_preserved=traceability.original_preserved,
    )


def build_equivalence_record(
    *,
    catalog_view: NormalizedConceptCatalogView,
    concepts: tuple[NormalizedConceptRecord, ...],
    sequence: int,
    relation_type: EquivalenceRelationType,
    evidence_level: EvidenceLevel,
    detector_type: str,
    detector_name: str,
    criteria_used: tuple[str, ...],
    information_used: tuple[str, ...],
    limitations: tuple[str, ...],
    rationale: str,
    metadata: dict[str, Any] | None = None,
) -> EquivalenceRecord:
    return EquivalenceRecord(
        equivalence_id=build_equivalence_id(catalog_view.model_id, sequence),
        involved_concept_ids=tuple(concept.normalized_concept_id for concept in concepts),
        relation_type=relation_type.value,
        evidence_level=evidence_level.value,
        status=EquivalenceDetectionStatus.DETECTED.value,
        detector_type=detector_type,
        explainability=EquivalenceExplainability(
            criteria_used=criteria_used,
            information_used=information_used,
            limitations=limitations,
            rationale=rationale,
        ),
        traceability=build_equivalence_traceability(
            catalog_view=catalog_view,
            concepts=concepts,
        ),
        metadata={
            "detector_name": detector_name,
            **(metadata or {}),
        },
    )


def build_equivalence_catalog(
    *,
    catalog_view: NormalizedConceptCatalogView,
    equivalences: tuple[EquivalenceRecord, ...],
    comparable_group_builder_prepared: bool,
    context_association_prepared: bool,
    comparative_domain_model_prepared: bool,
) -> EquivalenceCatalog:
    document_ids = tuple(
        dict.fromkeys(
            document_id
            for equivalence in equivalences
            for document_id in equivalence.traceability.document_ids
            if document_id
        )
    )

    if not document_ids:
        document_ids = (
            catalog_view.document_id,
        )

    return EquivalenceCatalog(
        catalog_id=f"ede-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_normalized_catalog_id=catalog_view.catalog_id,
        equivalences=equivalences,
        document_ids=document_ids,
        comparable_group_builder_prepared=comparable_group_builder_prepared,
        context_association_prepared=context_association_prepared,
        comparative_domain_model_prepared=comparative_domain_model_prepared,
    )