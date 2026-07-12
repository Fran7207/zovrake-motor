"""Adaptadores documentales iniciales — estructuras preparadas."""

from zovrake_motor.comprehension.adapters.implementations.excel import ExcelDocumentAdapter
from zovrake_motor.comprehension.adapters.implementations.image import ImageDocumentAdapter
from zovrake_motor.comprehension.adapters.implementations.pdf import PdfDocumentAdapter
from zovrake_motor.comprehension.adapters.implementations.word import WordDocumentAdapter

__all__ = [
    "ExcelDocumentAdapter",
    "ImageDocumentAdapter",
    "PdfDocumentAdapter",
    "WordDocumentAdapter",
]
