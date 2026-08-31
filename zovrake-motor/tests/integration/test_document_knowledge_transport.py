"""Prueba extremo a extremo del transporte de DocumentKnowledge."""

from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)
from zovrake_motor.motor_runtime.document_content import (
    resolve_evidence_documents,
)
from zovrake_motor.motor_runtime.result_registry import (
    AnalysisResultRegistry,
)


# test_document_knowledge_transport.py
# está en:
#
#   <proyecto>/tests/integration/
#
# Por ello:
#   parents[0] = integration
#   parents[1] = tests
#   parents[2] = raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_PDFS = (
    PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION.pdf",
    PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION-02.pdf",
)


def _data_url_from_file(path: Path) -> str:
    raw = path.read_bytes()

    return (
        "data:application/pdf;base64,"
        + base64.b64encode(raw).decode("ascii")
    )


def _build_documents() -> tuple[
    dict[str, object],
    ...
]:
    documents: list[dict[str, object]] = []

    for index, pdf_path in enumerate(
        TEST_PDFS,
        start=1,
    ):
        assert pdf_path.exists(), (
            f"No se encontró la fixture PDF: {pdf_path}"
        )

        documents.append(
            {
                "document_id": (
                    f"knowledge-transport-{index:03d}"
                ),
                "document_label": pdf_path.name,
                "content_type": "application/pdf",
                "metadata": {
                    "file_name": pdf_path.name,
                    "content_data_url": _data_url_from_file(
                        pdf_path
                    ),
                },
            }
        )

    return tuple(documents)


def test_document_knowledge_reaches_internal_model() -> None:
    """
    Verifica el trayecto completo:

        PDF
        -> DocumentKnowledge
        -> ContentExtractionResult
        -> Canonical
        -> InternalModel

    El conocimiento debe conservarse sin depender de una reconstrucción
    posterior del PDF.
    """
    documents = resolve_evidence_documents(
        _build_documents()
    )

    executor = CotizacionesAnalysisExecutor(
        result_registry=AnalysisResultRegistry(),
    )

    executor.initialize()

    process_id = uuid4()

    internal_models = (
        executor._run_comprehension_for_documents(
            process_id=process_id,
            documents=documents,
            codigo_req="ZO-0183",
            requirement_description=(
                "Validación de transporte extremo a extremo "
                "del conocimiento documental."
            ),
        )
    )

    assert len(internal_models) == len(
        TEST_PDFS
    )

    for model in internal_models:
        metadata_entity = model.get(
            "metadata"
        )

        assert isinstance(
            metadata_entity,
            dict,
        )

        extraction_metadata = metadata_entity.get(
            "extraction_metadata"
        )

        assert isinstance(
            extraction_metadata,
            dict,
        )

        document_knowledge = extraction_metadata.get(
            "document_knowledge"
        )

        assert isinstance(
            document_knowledge,
            dict,
        )

        assert document_knowledge.get(
            "document_id"
        ) == model.get(
            "document_id"
        )

        assert document_knowledge.get(
            "regions"
        )

        assert document_knowledge.get(
            "evidence"
        )

        assert document_knowledge.get(
            "facts"
        ) is not None

        assert document_knowledge.get(
            "attributes"
        ) is not None

        assert document_knowledge.get(
            "entities"
        ) is not None

        assert document_knowledge.get(
            "relationships"
        ) is not None

        knowledge_metadata = document_knowledge.get(
            "metadata"
        )

        assert isinstance(
            knowledge_metadata,
            dict,
        )

        assert knowledge_metadata.get(
            "semantic_model_version"
        )

        assert (
            extraction_metadata.get(
                "document_knowledge_entity_count"
            )
            == len(
                document_knowledge.get(
                    "entities",
                    (),
                )
                or ()
            )
        )

        assert (
            extraction_metadata.get(
                "document_knowledge_fact_count"
            )
            == len(
                document_knowledge.get(
                    "facts",
                    (),
                )
                or ()
            )
        )

        assert (
            extraction_metadata.get(
                "document_knowledge_relationship_count"
            )
            == len(
                document_knowledge.get(
                    "relationships",
                    (),
                )
                or ()
            )
        )