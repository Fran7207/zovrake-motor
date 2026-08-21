"""Prueba de clasificación documental multi-documento del Motor de Cotizaciones."""

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_PDFS = (
    PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION.pdf",
    PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION-02.pdf",
)


def _data_url_from_file(path: Path) -> str:
    """Convierte un PDF real en un data URL base64."""
    raw = path.read_bytes()

    return (
        "data:application/pdf;base64,"
        + base64.b64encode(raw).decode("ascii")
    )


def _build_evidence_documents() -> tuple[dict[str, object], ...]:
    """Construye las referencias documentales de los dos PDFs reales."""
    documents: list[dict[str, object]] = []

    for index, pdf_path in enumerate(TEST_PDFS, start=1):
        assert pdf_path.exists(), (
            f"No se encontró el PDF de prueba: {pdf_path}"
        )

        documents.append(
            {
                "document_id": f"executor-pdf-{index:03d}",
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


def test_cotizaciones_executor_builds_independent_document_classification() -> None:
    """
    Verifica que dos cotizaciones reales produzcan:

        2 documentos
        2 InternalModels
        2 catálogos normalizados
        1 snapshot colectivo

    sin ejecutar todavía equivalencias ni grupos comparables.
    """
    evidence_documents = _build_evidence_documents()

    resolved_documents = resolve_evidence_documents(
        evidence_documents
    )

    assert len(resolved_documents) == 2

    process_id = uuid4()

    executor = CotizacionesAnalysisExecutor(
        result_registry=AnalysisResultRegistry(),
    )

    executor.initialize()

    internal_models = executor._run_comprehension_for_documents(
        process_id=process_id,
        documents=resolved_documents,
        codigo_req="TEST-PDF-03B",
        requirement_description="Prueba de clasificación documental multi-documento",
    )

    assert len(internal_models) == 2

    internal_document_ids = [
        str(model.get("document_id", ""))
        for model in internal_models
    ]

    assert all(internal_document_ids)
    assert len(set(internal_document_ids)) == 2

    normalized_catalogs = tuple(
        executor._run_document_classification(
            process_id=process_id,
            internal_model=internal_model,
            codigo_req="TEST-PDF-03B",
            requirement_description=(
                "Prueba de clasificación documental multi-documento"
            ),
        )
        for internal_model in internal_models
    )

    assert len(normalized_catalogs) == 2

    normalized_document_ids = [
        str(
            catalog.get(
                "document_id",
                "",
            )
        )
        for catalog in normalized_catalogs
    ]

    assert all(normalized_document_ids)
    assert len(set(normalized_document_ids)) == 2

    assert set(normalized_document_ids) == set(
        internal_document_ids
    )

    snapshot = executor._build_document_classification_snapshot(
        process_id=process_id,
        normalized_catalogs=normalized_catalogs,
    )

    assert snapshot["document_count"] == 2
    assert snapshot["stage"] == (
        "normalized_document_classification"
    )

    assert snapshot["equivalence_executed"] is False
    assert snapshot["comparable_groups_executed"] is False
    assert snapshot["source_data_preserved"] is True

    snapshot_documents = snapshot["documents"]

    assert len(snapshot_documents) == 2

    snapshot_document_ids = {
        str(document["document_id"])
        for document in snapshot_documents
    }

    assert snapshot_document_ids == set(
        normalized_document_ids
    )

    snapshot_file_names = {
        str(document["file_name"])
        for document in snapshot_documents
    }

    expected_file_names = {
        pdf_path.name
        for pdf_path in TEST_PDFS
    }

    assert snapshot_file_names == expected_file_names