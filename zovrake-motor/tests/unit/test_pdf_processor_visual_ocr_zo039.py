from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from zovrake_motor.comprehension.pdf_processing.processor import PDFDocumentProcessor


def _font():
    for path in ("C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, 48)
        except OSError:
            pass
    return ImageFont.load_default()


def _pdf_with_text_inside_image() -> bytes:
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((100, 100), "GRUPO PROVEEDOR EJEMPLO S.A.C.", fill="black", font=_font())
    draw.text((100, 220), "RUC 20123456789", fill="black", font=_font())
    output = BytesIO()
    image.save(output, format="PDF", resolution=150.0)
    return output.getvalue()


def test_visual_ocr_mode_reads_text_inside_image_pages() -> None:
    document = PDFDocumentProcessor(ocr_visual_pages=True).process(
        document_id="ZO039-VISUAL-001",
        file_name="visual-provider.pdf",
        pdf_bytes=_pdf_with_text_inside_image(),
    )

    assert document.ocr_executed is True
    assert document.ocr_pages_executed == (1,)
    assert "GRUPO PROVEEDOR" in document.pages[0].ocr_text.upper()
    assert document.pages[0].ocr_blocks
