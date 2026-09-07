"""Procesamiento documental profundo de PDF."""

from zovrake_motor.comprehension.pdf_processing.models import (
    PdfImage,
    PdfStructuralObject,
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
    "PdfStructuralObject",
    "PdfPageAnalysis",
    "PdfTable",
    "PdfTextBlock",
    "ProcessedPdfDocument",
]
