from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from zovrake_motor.comprehension.pdf_processing.ocr import OcrProcessor
from zovrake_motor.comprehension.pdf_processing.processor import PDFDocumentProcessor


def _ocr_pdf() -> bytes:
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 80), "PROVEEDOR EJEMPLO S.A.C.", fill="black")
    draw.text((80, 150), "RUC 20123456789", fill="black")
    draw.text((80, 220), "COTIZACION 12345", fill="black")
    draw.rectangle((60, 40, 900, 300), outline="black", width=3)
    out = BytesIO()
    image.save(out, format="PDF", resolution=150)
    return out.getvalue()


def test_ocr_executes_multiple_layout_passes_and_preserves_render_identity() -> None:
    result = OcrProcessor(dpi=120, multi_pass=True, upscale_factor=1.25).process_page(
        pdf_bytes=_ocr_pdf(),
        page_number=1,
    )

    assert result.render_sha256
    assert result.render_width_px
    assert result.render_height_px
    assert result.passes_executed == (6, 3, 11)
    assert "PROVEEDOR" in result.text.upper()


def test_pdf_processor_exposes_visual_capture_coverage_separately_from_ocr_coverage() -> None:
    document = PDFDocumentProcessor(
        ocr_visual_pages=True,
        ocr_all_pages=True,
        ocr_embedded_images=True,
    ).process(
        document_id="ZO050-001",
        file_name="coverage.pdf",
        pdf_bytes=_ocr_pdf(),
    )

    assert document.page_count == 1
    assert document.visual_render_page_count == 1
    assert len(document.visual_rendered_page_hashes) == 1
    assert document.pages[0].visual_render_sha256
    assert document.pages[0].ocr_passes_executed == (6, 3, 11)
    assert document.coverage["visual_capture_page_count"] == 1
    assert document.coverage["visual_ocr_page_count"] == 1
    assert document.coverage["low_confidence_ocr_page_count"] >= 0
