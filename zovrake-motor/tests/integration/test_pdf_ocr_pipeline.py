"""Pruebas de integración del OCR real del procesamiento PDF."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _test_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )

    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), 60)

    return ImageFont.load_default()


def _build_scanned_pdf() -> bytes:
    image = Image.new("RGB", (1600, 1000), "white")
    draw = ImageDraw.Draw(image)
    font = _test_font()

    draw.text(
        (100, 100),
        "COTIZACION MATERIAL CEMENTO",
        font=font,
        fill="black",
    )
    draw.text(
        (100, 220),
        "10 UNIDADES PRECIO 25.50",
        font=font,
        fill="black",
    )

    output = BytesIO()
    image.save(output, format="PDF", resolution=150.0)
    return output.getvalue()


def test_real_ocr_executes_on_image_only_pdf() -> None:
    document = PDFDocumentProcessor().process(
        document_id="OCR-REAL-001",
        file_name="scan.pdf",
        pdf_bytes=_build_scanned_pdf(),
    )

    page = document.pages[0]

    assert document.ocr_required is True
    assert document.ocr_executed is True
    assert document.ocr_pages_executed == (1,)
    assert document.ocr_confidence > 0.0
    assert document.ocr_language == "spa+eng"
    assert document.extraction_method == "native_pdf+ocr"

    assert "COTIZACION" in page.ocr_text.upper()
    assert page.ocr_blocks
    assert page.ocr_blocks[0].confidence > 0.0

    # Los bloques utilizados por el análisis de layout incluyen OCR
    # cuando no existe una representación nativa suficiente.
    assert page.text_blocks
    assert any(
        block.text.strip()
        for block in page.text_blocks
    )


def test_digital_fixture_does_not_execute_ocr() -> None:
    pdf_path = (
        PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "COTIZACION.pdf"
    )

    document = PDFDocumentProcessor().process(
        document_id="OCR-CONTROL-001",
        file_name=pdf_path.name,
        pdf_bytes=pdf_path.read_bytes(),
    )

    assert document.ocr_required is False
    assert document.ocr_executed is False
    assert document.ocr_pages_executed == ()
    assert document.extraction_method == "native_pdf"
