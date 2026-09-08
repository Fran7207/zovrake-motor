from pathlib import Path

from zovrake_motor.comprehension.document_knowledge_builder import DocumentKnowledgeBuilder
from zovrake_motor.comprehension.pdf_processing.processor import PDFDocumentProcessor


def test_capture_audit_distinguishes_capture_from_recognition():
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / "COTIZACION.pdf"
    document = PDFDocumentProcessor(
        ocr_visual_pages=True,
        ocr_all_pages=True,
        ocr_embedded_images=True,
    ).process(
        document_id=pdf.name,
        file_name=pdf.name,
        pdf_bytes=pdf.read_bytes(),
    )

    audit = document.capture_audit
    assert audit["status"] == "complete"
    assert audit["interpretation"]["capture_complete"] is True
    assert audit["page_count"] == document.page_count
    assert audit["rendered_page_count"] == document.page_count
    assert audit["visual_understanding_completed_page_count"] == document.page_count
    assert audit["reading_order_entry_count"] == len(document.reading_order)
    assert audit["image_count"] == len(document.images)
    assert "recognition_gaps" in audit

    knowledge = DocumentKnowledgeBuilder().build(document)
    assert knowledge.capture_audit == document.capture_audit
    assert knowledge.metadata["source_capture_audit"] == document.capture_audit
