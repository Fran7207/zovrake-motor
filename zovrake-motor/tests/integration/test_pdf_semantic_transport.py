"""Certificación de transporte semántico PDF."""

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
    raw = path.read_bytes()
    return (
        "data:application/pdf;base64,"
        + base64.b64encode(raw).decode("ascii")
    )


def test_pdf_semantic_tables_survive_document_content_resolution() -> None:
    """Verifica que la semántica PDF llegue íntegra al contenido resuelto."""

    evidence_documents = tuple(
        {
            "document_id": f"semantic-test-{index + 1:03d}",
            "document_label": pdf_path.name,
            "content_type": "application/pdf",
            "metadata": {
                "file_name": pdf_path.name,
                "content_data_url": _data_url_from_file(pdf_path),
            },
        }
        for index, pdf_path in enumerate(TEST_PDFS)
    )

    documents = resolve_evidence_documents(evidence_documents)

    assert len(documents) == len(TEST_PDFS)

    for document, pdf_path in zip(
        documents,
        TEST_PDFS,
        strict=True,
    ):
        processing = document.metadata.get("pdf_processing")

        assert isinstance(processing, dict)
        assert processing["status"] in {
            "processed",
            "processed_with_errors",
            "fallback_legacy_extractor",
        }

        # Si el procesador produjo semántica, debe conservarse también
        # en ResolvedDocumentContent.
        expected_semantic_tables = tuple(
            processing.get("semantic_tables") or ()
        )

        assert tuple(document.semantic_tables) == expected_semantic_tables
        assert document.to_summary()["semantic_tables_count"] == len(
            document.semantic_tables
        )

        adapter_metadata = document.to_adapter_metadata()

        assert tuple(
            adapter_metadata["semantic_tables"]
        ) == tuple(document.semantic_tables)

        # Cuando existe semántica, sus elementos fundamentales deben
        # mantenerse intactos durante el transporte.
        for semantic in document.semantic_tables:
            assert "table_id" in semantic
            assert "columns" in semantic
            assert "rows" in semantic
            assert "confidence" in semantic
            assert "source_page_number" in semantic
            assert "evidence" in semantic

            assert isinstance(semantic["columns"], list)
            assert isinstance(semantic["rows"], list)
            assert isinstance(semantic["confidence"], (int, float))
            assert isinstance(semantic["evidence"], list)

        assert document.file_name == pdf_path.name
        assert document.text_content.strip()
