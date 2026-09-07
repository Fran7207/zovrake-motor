from io import BytesIO

from PIL import Image, ImageDraw

from zovrake_motor.comprehension.pdf_processing.visual_understanding import (
    MultimodalVisualUnderstandingEngine,
)


def _png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_local_visual_engine_preserves_text_and_semantic_hints():
    image = Image.new("RGB", (800, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 30), "CORPORACION EJEMPLO S.A.C. RUC 20123456789", fill="black")
    draw.rectangle((20, 100, 760, 250), outline="black", width=4)

    result = MultimodalVisualUnderstandingEngine().analyze_image_bytes(
        image_bytes=_png_bytes(image),
        detected_text="CORPORACION EJEMPLO S.A.C. RUC 20123456789",
        page_number=1,
        source_id="test-image",
    )

    assert result.analysis_status == "completed"
    assert "supplier_identity" in result.semantic_hints
    assert "text_present" in result.detected_features
    assert result.visual_confidence > 0
    assert result.detected_text.startswith("CORPORACION")


def test_local_visual_engine_detects_qr_without_external_model():
    import qrcode

    qr = qrcode.QRCode(box_size=8, border=3)
    qr.add_data("https://zovrake.local/test")
    qr.make(fit=True)
    image = qr.make_image().convert("RGB")

    result = MultimodalVisualUnderstandingEngine().analyze_image_bytes(
        image_bytes=_png_bytes(image),
        page_number=1,
        source_id="qr-test",
    )

    assert result.analysis_status == "completed"
    assert result.object_type == "qr_code"
    assert "https://zovrake.local/test" in result.qr_codes
    assert "qr_code" in result.detected_features
