"""Pruebas de integración del procesamiento documental PDF."""

from __future__ import annotations

import base64
from pathlib import Path

from zovrake_motor.motor_runtime.document_content import (
    resolve_evidence_documents,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_PDF = PROJECT_ROOT / "tests" / "fixtures" / "COTIZACION.pdf"


def _data_url_from_file(path: Path) -> str:
    raw = path.read_bytes()

    return (
        "data:application/pdf;base64,"
        + base64.b64encode(raw).decode("ascii")
    )


def test_pdf_document_pipeline_real() -> None:
    assert TEST_PDF.exists(), (
        f"No se encontró el PDF de prueba: {TEST_PDF}"
    )

    data_url = _data_url_from_file(TEST_PDF)

    documents = resolve_evidence_documents(
        (
            {
                "document_id": "pdf-test-001",
                "document_label": TEST_PDF.name,
                "content_type": "application/pdf",
                "metadata": {
                    "file_name": TEST_PDF.name,
                    "content_data_url": data_url,
                },
            },
        )
    )

    assert len(documents) == 1

    document = documents[0]

    assert document.document_id == "pdf-test-001"
    assert document.content_type == "application/pdf"
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
        range(1, processing["page_count"] + 1)
    )