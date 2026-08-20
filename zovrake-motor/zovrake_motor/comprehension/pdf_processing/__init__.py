"""Procesamiento documental profundo de PDF."""

from zovrake_motor.comprehension.pdf_processing.models import (
    PdfImage,
    PdfPageAnalysis,
    PdfTable,
    PdfTextBlock,
    ProcessedPdfDocument,
)
from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)

__all__ = [
    "PDFDocumentProcessor",
    "PdfImage",
    "PdfPageAnalysis",
    "PdfTable",
    "PdfTextBlock",
    "ProcessedPdfDocument",
]
