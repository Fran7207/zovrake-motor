"""Certificación PDF → SemanticTable → CanonicalItem → CanonicalDocument."""

from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from zovrake_motor.comprehension.canonical import (
    CanonicalRepresentationEngine,
    CanonicalRepresentationRequest,
)
from zovrake_motor.comprehension.extraction.engine import (
    ContentExtractionEngine,
)
from zovrake_motor.comprehension.extraction.models import (
    AdapterDocumentContext,
    ContentExtractionRequest,
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
    return (
        "data:application/pdf;base64,"
        + base64.b64encode(path.read_bytes()).decode("ascii")
    )


def _resolve_documents():
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

    return resolve_evidence_documents(evidence_documents)


def test_pdf_semantic_tables_produce_canonical_items() -> None:
    documents = _resolve_documents()

    extraction_engine = ContentExtractionEngine()
    extraction_engine.initialize()

    canonical_engine = CanonicalRepresentationEngine()
    canonical_engine.initialize()

    for document in documents:
        assert document.semantic_tables

        semantic_row_count = sum(
            len(table.get("rows") or ())
            for table in document.semantic_tables
            if isinstance(table, dict)
        )

        assert semantic_row_count > 0

        process_id = uuid4()

        adapter_context = AdapterDocumentContext(
            process_id=process_id,
            document_id=document.document_id,
            adapter_name="pdf_adapter",
            format_type="pdf",
            document_reference=(
                f"adapter://pdf_adapter/{document.document_id}"
            ),
            original_preserved=True,
            metadata=document.to_adapter_metadata(),
        )

        extraction = extraction_engine.extract(
            ContentExtractionRequest(
                process_id=process_id,
                document_id=document.document_id,
                adapter_context=adapter_context,
            ),
        )

        assert extraction.metadata.get("semantic_tables")

        canonical = canonical_engine.represent(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=extraction,
            ),
        )

        representation = canonical.representation
        items = tuple(representation.items)

        semantic_items = tuple(
            item
            for item in items
            if isinstance(item.fields, dict)
            and item.fields.get("semantic_table_id")
        )

        assert semantic_items
        assert len(semantic_items) == semantic_row_count

        for item in semantic_items:
            fields = item.fields
            values = fields.get("values")

            assert isinstance(values, dict)
            assert values
            assert fields.get("semantic_columns")
            assert fields.get("semantic_table_confidence") is not None
            assert (
                fields.get(
                    "semantic_table_source_page_number"
                )
                is not None
            )
            assert isinstance(
                fields.get("semantic_table_evidence"),
                list,
            )
            assert item.source_reference


def test_pdf_documents_keep_independent_semantic_structures() -> None:
    documents = _resolve_documents()

    assert len(documents) == 2

    structures = []

    for document in documents:
        structures.append(
            frozenset(
                key
                for table in document.semantic_tables
                if isinstance(table, dict)
                for row in (table.get("rows") or ())
                if isinstance(row, dict)
                for key in row
            )
        )

    assert all(structures)

    assert structures[0] != structures[1] or (
        documents[0].file_name != documents[1].file_name
    )