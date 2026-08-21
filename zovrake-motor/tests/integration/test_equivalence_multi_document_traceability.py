"""Prueba de trazabilidad multi-documento del EDE."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.classification.concept_normalization.models import (
    NormalizedConceptRecord,
    NormalizedConceptTraceability,
    NormalizedModelReference,
)
from zovrake_motor.classification.equivalence_detection.builders import (
    build_equivalence_traceability,
)
from zovrake_motor.classification.equivalence_detection.gateway import (
    NormalizedConceptCatalogView,
)
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceTraceability,
)


PROCESS_ID = uuid4()


def _build_concept(
    *,
    concept_id: str,
    document_id: str,
) -> NormalizedConceptRecord:
    return NormalizedConceptRecord(
        normalized_concept_id=f"normalized-{concept_id}",
        original_value="Cemento Portland Tipo I",
        normalized_value="cemento portland tipo i",
        concept_type="material",
        source_category="material",
        concept_id=concept_id,
        model_reference=NormalizedModelReference(
            model_id=f"model-{document_id}",
            document_id=document_id,
            concept_id=concept_id,
            source_record_id=f"source-{concept_id}",
            source_category="material",
        ),
        traceability=NormalizedConceptTraceability(
            process_id=PROCESS_ID,
            document_id=document_id,
            model_id=f"model-{document_id}",
            concept_id=concept_id,
            source_material_catalog_id=(
                f"mce-catalog://{document_id}"
            ),
            source_service_catalog_id="",
            document_reference=(
                f"document://{document_id}"
            ),
            canonical_reference=(
                f"canonical://{document_id}"
            ),
            extraction_reference=(
                f"extraction://{document_id}"
            ),
            source_reference=(
                f"source://{concept_id}"
            ),
            adapter_name="pdf_adapter",
            format_type="pdf",
            original_preserved=True,
        ),
    )


def test_equivalence_traceability_preserves_all_involved_documents() -> None:
    concept_a = _build_concept(
        concept_id="concept-A",
        document_id="DOC-A",
    )

    concept_b = _build_concept(
        concept_id="concept-B",
        document_id="DOC-B",
    )

    concepts = (
        concept_a,
        concept_b,
    )

    catalog_view = NormalizedConceptCatalogView(
        catalog_id="catalog-multi-document",
        process_id=PROCESS_ID,
        model_id="multi-document-model",
        document_id="DOC-A",
        concepts=concepts,
        raw_catalog={
            "catalog_id": "catalog-multi-document",
            "process_id": str(PROCESS_ID),
            "model_id": "multi-document-model",
            "document_id": "DOC-A",
            "concepts": [
                concept_a.to_dict(),
                concept_b.to_dict(),
            ],
            "equivalence_detection_prepared": True,
        },
    )

    traceability = build_equivalence_traceability(
        catalog_view=catalog_view,
        concepts=concepts,
    )

    assert isinstance(
        traceability,
        EquivalenceTraceability,
    )

    assert traceability.document_id == "DOC-A"

    assert traceability.document_ids == (
        "DOC-A",
        "DOC-B",
    )

    assert traceability.concept_ids == (
        "concept-A",
        "concept-B",
    )

    serialized = traceability.to_dict()

    assert serialized["document_id"] == "DOC-A"

    assert serialized["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    assert serialized["concept_ids"] == [
        "concept-A",
        "concept-B",
    ]