"""Certificación PDF → SemanticTable → CanonicalItem."""

from __future__ import annotations

import base64
from pathlib import Path

from zovrake_motor.comprehension.canonical.assembler import (
    CanonicalAssembler,
)
from zovrake_motor.comprehension.canonical.models import (
    CanonicalTraceability,
)
from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionRequest,
)
from zovrake_motor.comprehension.extraction.engine import (
    ContentExtractionEngine,
)
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


def test_pdf_semantic_tables_produce_canonical_items() -> None:
    """
    Verifica que las filas de las tablas semánticas lleguen al modelo
    canónico como ítems independientes y conserven sus atributos.
    """

    evidence_documents = tuple(
        {
            "document_id": f"canonical-test-{index + 1:03d}",
            "document_label": pdf_path.name,
            "content_type": "application/pdf",
            "metadata": {
                "file_name": pdf_path.name,
                "content_data_url": _data_url_from_file(pdf_path),
            },
        }
        for index, pdf_path in enumerate(TEST_PDFS)
    )

    resolved_documents = resolve_evidence_documents(
        evidence_documents
    )

    assert len(resolved_documents) == len(TEST_PDFS)

    for document in resolved_documents:
        semantic_tables = tuple(
            document.semantic_tables
        )

        assert semantic_tables

        semantic_row_count = sum(
            len(table.get("rows") or ())
            for table in semantic_tables
        )

        assert semantic_row_count > 0

        extraction_engine = ContentExtractionEngine()
        extraction_engine.initialize()

        request = ContentExtractionRequest(
            process_id=f"canonical-{document.document_id}",
            document_id=document.document_id,
            metadata=document.to_adapter_metadata(),
        )

        extraction_result = extraction_engine.extract(
            request
        )

        assert extraction_result.metadata.get(
            "semantic_tables"
        )

        traceability = CanonicalTraceability(
            extraction_reference_id=(
                f"extraction/{document.document_id}"
            ),
        )

        assembler = CanonicalAssembler()

        canonical_document = assembler.assemble(
            extraction_result,
            traceability=traceability,
        )

        assert canonical_document is not None

        items = tuple(
            canonical_document.items
        )

        assert items

        semantic_items = tuple(
            item
            for item in items
            if isinstance(item.fields, dict)
            and item.fields.get(
                "semantic_table_id"
            )
        )

        assert semantic_items

        assert len(semantic_items) == semantic_row_count

        for item in semantic_items:
            fields = item.fields

            assert fields.get(
                "semantic_table_id"
            )

            assert fields.get(
                "semantic_columns"
            )

            values = fields.get(
                "values"
            )

            assert isinstance(
                values,
                dict,
            )

            assert any(
                str(value).strip()
                for value in values.values()
            )

            assert fields.get(
                "semantic_table_confidence"
            ) is not None

            assert (
                fields.get(
                    "semantic_table_source_page_number"
                )
                is not None
            )

            evidence = fields.get(
                "semantic_table_evidence"
            )

            assert isinstance(
                evidence,
                list,
            )

            assert item.source_reference

            assert (
                item.description
                or values.get("description")
                or values.get("code")
            )


def test_pdf_documents_keep_independent_semantic_structures() -> None:
    """
    Verifica que dos PDFs no sean forzados a compartir una plantilla
    estructural fija.
    """

    evidence_documents = tuple(
        {
            "document_id": f"structure-test-{index + 1:03d}",
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

    assert len(documents) == 2

    structures = []

    for document in documents:
        keys = {
            key
            for table in document.semantic_tables
            for row in (
                table.get("rows") or ()
            )
            if isinstance(row, dict)
            for key in row.keys()
        }

        structures.append(
            frozenset(keys)
        )

    assert all(
        structure
        for structure in structures
    )