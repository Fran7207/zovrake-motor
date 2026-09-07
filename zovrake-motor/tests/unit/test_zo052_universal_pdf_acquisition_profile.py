from zovrake_motor.comprehension.pdf_processing.processor import PDFDocumentProcessor


def test_default_pdf_processor_uses_exhaustive_visual_acquisition_profile():
    processor = PDFDocumentProcessor()

    assert processor._ocr_all_pages is True
    assert processor._ocr_embedded_images is True
    assert processor._ocr_visual_pages is True
