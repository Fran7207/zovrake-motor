"""Utilidades de construcción de conceptos y trazabilidad."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_analysis.enums import (
    ConceptAnalysisStatus,
    ConceptKind,
)
from zovrake_motor.classification.concept_analysis.gateway import (
    InternalModelView,
)
from zovrake_motor.classification.concept_analysis.models import (
    ConceptCandidate,
    ConceptLocation,
    ConceptTraceability,
)


def build_traceability(
    model_view: InternalModelView,
) -> ConceptTraceability:
    traceability = model_view.traceability
    original = model_view.original_references

    return ConceptTraceability(
        process_id=model_view.process_id,
        document_id=model_view.document_id,
        model_id=model_view.model_id,
        document_reference=str(
            traceability.get(
                "document_reference",
                original.get(
                    "document_reference",
                    "",
                ),
            ),
        ),
        adapter_name=str(
            traceability.get(
                "adapter_name",
                original.get(
                    "adapter_name",
                    "",
                ),
            ),
        ),
        format_type=str(
            traceability.get(
                "format_type",
                original.get(
                    "format_type",
                    "",
                ),
            ),
        ),
        original_preserved=bool(
            traceability.get(
                "original_preserved",
                original.get(
                    "original_preserved",
                    True,
                ),
            ),
        ),
    )


def build_concept_id(
    model_id: str,
    sequence: int,
) -> str:
    return (
        f"cae://{model_id}/concept-{sequence:04d}"
    )


def build_concept(
    *,
    model_view: InternalModelView,
    sequence: int,
    kind: ConceptKind,
    original_description: str,
    section: str,
    entity_id: str,
    source_reference: str,
    canonical_reference: str,
    extraction_reference: str,
    entity_index: int | None = None,
    field_name: str = "",
    metadata: dict[str, Any] | None = None,
) -> ConceptCandidate:
    description = original_description.strip()

    return ConceptCandidate(
        concept_id=build_concept_id(
            model_view.model_id,
            sequence,
        ),
        kind=kind,
        original_description=description,
        location=ConceptLocation(
            section=section,
            entity_id=entity_id,
            entity_index=entity_index,
            field_name=field_name,
            source_reference=source_reference,
            canonical_reference=canonical_reference,
            extraction_reference=extraction_reference,
        ),
        traceability=build_traceability(
            model_view
        ),
        status=(
            ConceptAnalysisStatus.IDENTIFIED
            if description
            else ConceptAnalysisStatus.SKIPPED
        ),
        classification_pending=True,
        metadata=metadata or {},
    )