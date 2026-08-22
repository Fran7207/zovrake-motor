"""Prueba de integración real EDE → CGB multi-documento."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)
from zovrake_motor.motor_runtime.result_registry import AnalysisResultRegistry


PROCESS_ID = uuid4()


def _concept(document_id: str, concept_id: str) -> dict:
    return {
        "normalized_concept_id": f"normalized-{concept_id}",
        "original_value": "Cemento Portland Tipo I",
        "normalized_value": "cemento portland tipo i",
        "concept_type": "material",
        "source_category": "material",
        "concept_id": concept_id,
        "model_reference": {
            "model_id": f"model-{document_id}",
            "document_id": document_id,
            "concept_id": concept_id,
            "source_record_id": f"source-{concept_id}",
            "source_category": "material",
        },
        "traceability": {
            "process_id": str(PROCESS_ID),
            "document_id": document_id,
            "model_id": f"model-{document_id}",
            "concept_id": concept_id,
            "source_material_catalog_id": f"material://{document_id}",
            "source_service_catalog_id": "",
            "document_reference": f"document://{document_id}",
            "canonical_reference": f"canonical://{document_id}",
            "extraction_reference": f"extraction://{document_id}",
            "source_reference": f"source://{concept_id}",
            "adapter_name": "pdf_adapter",
            "format_type": "pdf",
            "original_preserved": True,
        },
        "status": "normalized",
        "metadata": {},
    }


def _collective_catalog() -> dict:
    return {
        "catalog_id": f"cne-collective://{PROCESS_ID}",
        "process_id": str(PROCESS_ID),
        "model_id": f"collective-model://{PROCESS_ID}",
        "document_id": f"multi-document://{PROCESS_ID}",
        "document_ids": ["DOC-A", "DOC-B"],
        "document_count": 2,
        "source_catalog_ids": ["CAT-A", "CAT-B"],
        "source_model_ids": ["MODEL-A", "MODEL-B"],
        "source_material_catalog_ids": [
            "material://DOC-A",
            "material://DOC-B",
        ],
        "source_service_catalog_ids": [],
        "concepts": [
            _concept("DOC-A", "CONCEPT-A"),
            _concept("DOC-B", "CONCEPT-B"),
        ],
        "concepts_count": 2,
        "equivalence_detection_prepared": True,
        "collective_normalization": True,
        "source_data_preserved": True,
    }


def test_collective_ede_to_cgb_preserves_multi_document_identity() -> None:
    executor = CotizacionesAnalysisExecutor(
        result_registry=AnalysisResultRegistry(),
    )
    executor.initialize()

    equivalence_catalog = executor._run_collective_equivalence_detection(
        process_id=PROCESS_ID,
        collective_normalized_catalog=_collective_catalog(),
    )

    assert equivalence_catalog["equivalences_count"] >= 1
    assert equivalence_catalog["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    equivalence = equivalence_catalog["equivalences"][0]
    assert equivalence["traceability"]["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    group_catalog = executor._run_collective_comparable_groups(
        process_id=PROCESS_ID,
        collective_equivalence_catalog=equivalence_catalog,
        codigo_req="TEST-PDF-03B-08",
    )

    assert group_catalog["groups_count"] >= 1
    assert group_catalog["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    group = group_catalog["groups"][0]

    assert group["model_reference"]["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    assert group["traceability"]["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    assert group["metadata"]["cross_document_group"] is True
    assert group["metadata"]["document_count"] == 2