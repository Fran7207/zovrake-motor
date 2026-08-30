"""Integración real: PDF -> DocumentKnowledge -> semántica."""

from __future__ import annotations

from pathlib import Path

from zovrake_motor.comprehension.document_knowledge_builder import (
    DocumentKnowledgeBuilder,
)
from zovrake_motor.comprehension.document_semantic_analyzer import (
    DocumentSemanticAnalyzer,
)
from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)


FIXTURES_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures"
)


def _process_fixture(
    file_name: str,
):
    pdf_path = FIXTURES_DIR / file_name

    assert pdf_path.exists(), (
        f"No existe la fixture PDF: {pdf_path}"
    )

    pdf_bytes = pdf_path.read_bytes()

    processor = PDFDocumentProcessor()

    processed = processor.process(
        document_id=file_name,
        file_name=file_name,
        pdf_bytes=pdf_bytes,
    )

    assert processed.successfully_processed is True
    assert processed.page_count > 0

    knowledge = DocumentKnowledgeBuilder().build(
        processed,
    )

    return (
        processed,
        DocumentSemanticAnalyzer().analyze(
            knowledge,
        ),
    )


def test_real_pdf_produces_unified_document_knowledge() -> None:
    processed, knowledge = _process_fixture(
        "COTIZACION.pdf",
    )

    assert knowledge.document_id == processed.document_id
    assert knowledge.file_name == processed.file_name
    assert knowledge.page_count == processed.page_count

    assert knowledge.text == processed.full_text

    assert len(knowledge.tables) == len(
        processed.tables
    )

    assert len(knowledge.images) == len(
        processed.images
    )

    assert len(knowledge.ocr_blocks) == sum(
        len(page.ocr_blocks)
        for page in processed.pages
    )

    assert len(knowledge.regions) > 0
    assert len(knowledge.evidence) > 0

    for region in knowledge.regions:
        assert region.page_number >= 1
        assert region.region_id
        assert region.source_kind

    for evidence in knowledge.evidence:
        assert evidence.evidence_id
        assert evidence.page_number >= 1


def test_real_pdf_semantic_analysis_preserves_all_regions() -> None:
    processed, knowledge = _process_fixture(
        "COTIZACION-02.pdf",
    )

    assert len(knowledge.regions) > 0

    original_region_count = len(
        knowledge.regions
    )

    analyzed_regions = [
        region
        for region in knowledge.regions
        if "document_section" in region.metadata
    ]

    assert len(analyzed_regions) == (
        original_region_count
    )

    assert knowledge.text == processed.full_text

    assert len(knowledge.tables) == len(
        processed.tables
    )

    assert len(knowledge.images) == len(
        processed.images
    )


def test_real_pdfs_generate_semantic_context_without_destroying_content() -> None:
    for file_name in (
        "COTIZACION.pdf",
        "COTIZACION-02.pdf",
    ):
        processed, knowledge = _process_fixture(
            file_name,
        )

        assert knowledge.regions

        # Como mínimo, el analizador debe haber evaluado
        # todas las regiones.
        analyzed_count = sum(
            1
            for region in knowledge.regions
            if "semantic_model_version"
            in region.metadata
        )

        assert analyzed_count == len(
            knowledge.regions
        )

        # Nunca sustituimos el texto original.
        assert knowledge.text == processed.full_text

        # Las estructuras físicas siguen disponibles.
        assert len(knowledge.tables) == len(
            processed.tables
        )
        assert len(knowledge.images) == len(
            processed.images
        )