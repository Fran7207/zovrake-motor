from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from zovrake_motor.comprehension.document_knowledge_builder import (
    DocumentKnowledgeBuilder,
)
from zovrake_motor.comprehension.pdf_processing.ocr import OcrProcessor
from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)


def _two_zone_pdf() -> bytes:
    image = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 80), "PROVEEDOR DEMO S.A.C.", fill="black")
    draw.text((80, 180), "RUC 20123456789", fill="black")
    draw.text((80, 300), "PRODUCTO EQUIPO 10 UND 250.00 2500.00", fill="black")
    draw.rectangle((60, 260, 1050, 390), outline="black", width=2)
    out = BytesIO()
    image.save(out, format="PDF", resolution=100)
    return out.getvalue()


def test_ocr_blocks_are_spatially_ordered() -> None:
    result = OcrProcessor(
        dpi=100,
        language="eng",
        psm=6,
        multi_pass=False,
        upscale_factor=1.0,
    ).process_page(
        pdf_bytes=_two_zone_pdf(),
        page_number=1,
    )

    assert result.blocks
    y_values = [block.bbox[1] for block in result.blocks]
    assert y_values == sorted(y_values)
    assert "PROVEEDOR" in result.text.upper()


def test_processor_emits_ordered_document_evidence() -> None:
    document = PDFDocumentProcessor(
        ocr_visual_pages=True,
        ocr_all_pages=False,
        ocr_embedded_images=True,
        ocr_processor=OcrProcessor(
            dpi=100,
            language="eng",
            psm=6,
            multi_pass=False,
            upscale_factor=1.0,
        ),
    ).process(
        document_id="ZO054-001",
        file_name="ordered.pdf",
        pdf_bytes=_two_zone_pdf(),
    )

    assert document.page_count == 1
    assert document.reading_order
    assert document.ordered_text
    assert [entry.sequence for entry in document.reading_order] == list(
        range(1, len(document.reading_order) + 1)
    )
    assert all(entry.page_number == 1 for entry in document.reading_order)

    knowledge = DocumentKnowledgeBuilder().build(document)
    assert knowledge.reading_order
    assert knowledge.ordered_text == document.ordered_text
    assert knowledge.metadata["source_reading_order_count"] == len(
        document.reading_order
    )
