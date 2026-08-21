"""Pruebas de integración del procesamiento documental PDF."""

from __future__ import annotations

import base64
from pathlib import Path

from zovrake_motor.motor_runtime.document_content import (
    resolve_evidence_documents,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_PDFS = (
    PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION.pdf",
    PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION-02.pdf",
)


def _data_url_from_file(path: Path) -> str:
    """Convierte un archivo PDF real en un data URL base64."""
    raw = path.read_bytes()

    return (
        "data:application/pdf;base64,"
        + base64.b64encode(raw).decode("ascii")
    )


def test_pdf_document_pipeline_multiple_documents() -> None:
    """Verifica el procesamiento independiente de dos PDFs reales."""

    for pdf_path in TEST_PDFS:
        assert pdf_path.exists(), (
            f"No se encontró el PDF de prueba: {pdf_path}"
        )

    evidence_documents = tuple(
        {
            "document_id": f"pdf-test-{index + 1:03d}",
            "document_label": pdf_path.name,
            "content_type": "application/pdf",
            "metadata": {
                "file_name": pdf_path.name,
                "content_data_url": _data_url_from_file(pdf_path),
            },
        }
        for index, pdf_path in enumerate(TEST_PDFS)
    )

    documents = resolve_evidence_documents(
        evidence_documents
    )

    # Deben existir exactamente dos documentos resueltos.
    assert len(documents) == 2

    document_ids = {
        document.document_id
        for document in documents
    }

    assert document_ids == {
        "pdf-test-001",
        "pdf-test-002",
    }

    # Cada PDF debe conservar su identidad y contenido de forma
    # independiente.
    for document, expected_pdf in zip(
        documents,
        TEST_PDFS,
        strict=True,
    ):
        assert document.content_type == "application/pdf"
        assert document.file_name == expected_pdf.name
        assert document.text_content.strip()

        processing = document.metadata.get(
            "pdf_processing"
        )

        assert isinstance(processing, dict)

        assert processing["status"] in {
            "processed",
            "processed_with_errors",
            "fallback_legacy_extractor",
        }

        assert processing["page_count"] >= 1

        assert "pages" in processing
        assert "warnings" in processing
        assert "errors" in processing

        assert document.tables or document.items

        page_numbers = {
            page["page_number"]
            for page in processing["pages"]
        }

        assert page_numbers == set(
            range(
                1,
                processing["page_count"] + 1,
            )
        )

    # Las dos identidades documentales deben ser diferentes.
    assert (
        documents[0].document_id
        != documents[1].document_id
    )

    # Los archivos físicos de prueba también deben ser diferentes.
    assert (
        documents[0].file_name
        != documents[1].file_name
    )