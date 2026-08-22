"""Prueba de integración del catálogo normalizado colectivo multi-documento."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)
from zovrake_motor.motor_runtime.result_registry import AnalysisResultRegistry


def _catalog(
    *,
    process_id: str,
    document_id: str,
    model_id: str,
    catalog_id: str,
    concepts: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "catalog_id": catalog_id,
        "process_id": process_id,
        "model_id": model_id,
        "document_id": document_id,
        "source_material_catalog_id": f"material://{document_id}",
        "source_service_catalog_id": f"service://{document_id}",
        "concepts": concepts,
    }


def _concept(
    *,
    concept_id: str,
    normalized_concept_id: str,
    document_id: str,
    model_id: str,
) -> dict[str, object]:
    return {
        "concept_id": concept_id,
        "normalized_concept_id": normalized_concept_id,
        "original_value": "Cemento Portland Tipo I",
        "normalized_value": "cemento portland tipo i",
        "concept_type": "material",
        "source_category": "material",
        "model_reference": {
            "document_id": document_id,
            "model_id": model_id,
            "concept_id": concept_id,
        },
        "traceability": {
            "document_id": document_id,
            "model_id": model_id,
        },
    }


def test_collective_normalized_catalog_preserves_document_identity() -> None:
    process_id = uuid4()

    catalog_a = _catalog(
        process_id=str(process_id),
        document_id="DOC-A",
        model_id="MODEL-A",
        catalog_id="CAT-A",
        concepts=[
            _concept(
                concept_id="A-1",
                normalized_concept_id="N-A-1",
                document_id="DOC-A",
                model_id="MODEL-A",
            )
        ],
    )

    catalog_b = _catalog(
        process_id=str(process_id),
        document_id="DOC-B",
        model_id="MODEL-B",
        catalog_id="CAT-B",
        concepts=[
            _concept(
                concept_id="B-1",
                normalized_concept_id="N-B-1",
                document_id="DOC-B",
                model_id="MODEL-B",
            )
        ],
    )

    executor = CotizacionesAnalysisExecutor(
        result_registry=AnalysisResultRegistry(),
    )

    collective = executor._build_collective_normalized_catalog(
        process_id=process_id,
        normalized_catalogs=(catalog_a, catalog_b),
    )

    assert collective["catalog_id"] == (
        f"cne-collective://{process_id}"
    )
    assert collective["process_id"] == str(process_id)
    assert collective["document_id"] == (
        f"multi-document://{process_id}"
    )
    assert collective["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]
    assert collective["document_count"] == 2

    assert collective["source_catalog_ids"] == [
        "CAT-A",
        "CAT-B",
    ]
    assert collective["source_model_ids"] == [
        "MODEL-A",
        "MODEL-B",
    ]

    assert collective["concepts_count"] == 2

    concepts = collective["concepts"]
    assert [
        concept["concept_id"]
        for concept in concepts
    ] == [
        "A-1",
        "B-1",
    ]

    assert [
        concept["traceability"]["document_id"]
        for concept in concepts
    ] == [
        "DOC-A",
        "DOC-B",
    ]

    assert collective["equivalence_detection_prepared"] is True
    assert collective["comparable_group_builder_prepared"] is False
    assert collective["collective_normalization"] is True
    assert collective["source_data_preserved"] is True


def test_collective_normalized_catalog_deduplicates_only_same_identity() -> None:
    process_id = uuid4()

    first = _catalog(
        process_id=str(process_id),
        document_id="DOC-A",
        model_id="MODEL-A",
        catalog_id="CAT-A",
        concepts=[
            _concept(
                concept_id="A-1",
                normalized_concept_id="N-A-1",
                document_id="DOC-A",
                model_id="MODEL-A",
            )
        ],
    )

    duplicate_same_identity = _catalog(
        process_id=str(process_id),
        document_id="DOC-A",
        model_id="MODEL-A",
        catalog_id="CAT-A-COPY",
        concepts=[
            _concept(
                concept_id="A-1",
                normalized_concept_id="N-A-1",
                document_id="DOC-A",
                model_id="MODEL-A",
            )
        ],
    )

    different_document = _catalog(
        process_id=str(process_id),
        document_id="DOC-B",
        model_id="MODEL-B",
        catalog_id="CAT-B",
        concepts=[
            _concept(
                concept_id="A-1",
                normalized_concept_id="N-A-1",
                document_id="DOC-B",
                model_id="MODEL-B",
            )
        ],
    )

    executor = CotizacionesAnalysisExecutor(
        result_registry=AnalysisResultRegistry(),
    )

    collective = executor._build_collective_normalized_catalog(
        process_id=process_id,
        normalized_catalogs=(
            first,
            duplicate_same_identity,
            different_document,
        ),
    )

    assert collective["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]
    assert collective["document_count"] == 2
    assert collective["concepts_count"] == 2

    identities = {
        (
            concept["traceability"]["document_id"],
            concept["traceability"]["model_id"],
            concept["concept_id"],
            concept["normalized_concept_id"],
        )
        for concept in collective["concepts"]
    }

    assert identities == {
        ("DOC-A", "MODEL-A", "A-1", "N-A-1"),
        ("DOC-B", "MODEL-B", "A-1", "N-A-1"),
    }