"""Procesamiento documental profundo de PDF."""

from zovrake_motor.comprehension.pdf_processing.models import (
    PdfImage,
    PdfReadingEntry,
    PdfStructuralObject,
    PdfPageAnalysis,
    PdfTable,
    PdfTextBlock,
    ProcessedPdfDocument,
)
from zovrake_motor.comprehension.pdf_processing.visual_understanding import (
    MultimodalVisualUnderstandingEngine,
    VisualUnderstandingResult,
)
from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)

__all__ = [
    "PDFDocumentProcessor",
    "PdfImage",
    "PdfReadingEntry",
    "PdfStructuralObject",
    "PdfPageAnalysis",
    "PdfTable",
    "PdfTextBlock",
    "ProcessedPdfDocument",
    "MultimodalVisualUnderstandingEngine",
    "VisualUnderstandingResult",
]
