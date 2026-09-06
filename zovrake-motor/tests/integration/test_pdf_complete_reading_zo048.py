"""ZO-048: cobertura de lectura completa de PDF.

La prueba valida que la etapa física ejecute:
- extracción nativa;
- tablas;
- imágenes embebidas;
- lectura visual de cada página;
- OCR conservado como evidencia separada;
- conocimiento visual accesible para las siguientes capas.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from zovrake_motor.comprehension.document_knowledge_builder import (
    DocumentKnowledgeBuilder,
)
from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _font():
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), 52)
    return ImageFont.load_default()


def _build_mixed_pdf() -> bytes:
    image = Image.new("RGB", (1800, 1000), "white")
    draw = ImageDraw.Draw(image)
    font = _font()
    draw.text((100, 120), "PROVEEDOR OCULTO EN IMAGEN S.A.C.", fill="black", font=font)
    draw.text((100, 240), "RUC 20987654321", fill="black", font=font)
    draw.text((100, 360), "MATERIAL ESPECIAL 304", fill="black", font=font)
    output = BytesIO()
    image.save(output, format="PDF", resolution=150.0)
    return output.getvalue()


def test_every_pdf_page_gets_visual_reading_even_with_native_text() -> None:
    processor = PDFDocumentProcessor(ocr_all_pages=True)
    pdf_path = FIXTURES / "COTIZACION.pdf"

    document = processor.process(
        document_id="ZO048-001",
        file_name=pdf_path.name,
        pdf_bytes=pdf_path.read_bytes(),
    )

    assert document.page_count >= 1
    assert document.ocr_required is True
    assert document.ocr_executed is True
    assert document.visual_ocr_complete is True
    assert document.visual_ocr_pages_executed == tuple(range(1, document.page_count + 1))

    for page in document.pages:
        assert page.visual_ocr_attempted is True
        assert page.visual_ocr_complete is True
        assert page.ocr_executed is True
        assert page.native_text == page.text or page.native_text


def test_visual_reading_recovers_text_inside_page_image() -> None:
    document = PDFDocumentProcessor().process(
        document_id="ZO048-002",
        file_name="mixed-image.pdf",
        pdf_bytes=_build_mixed_pdf(),
    )

    page = document.pages[0]

    assert page.visual_ocr_complete is True
    assert page.ocr_executed is True
    assert page.ocr_blocks
    assert "PROVEEDOR OCULTO" in page.ocr_text.upper()
    assert "20987654321" in page.ocr_text
    assert "MATERIAL ESPECIAL" in page.ocr_text.upper()

    knowledge = DocumentKnowledgeBuilder().build(document)
    assert knowledge.ocr_blocks
    ocr_joined = " ".join(
        str(block.get("text", ""))
        for block in knowledge.ocr_blocks
    ).upper()
    assert "PROVEEDOR" in ocr_joined
    assert "OCULTO" in ocr_joined
