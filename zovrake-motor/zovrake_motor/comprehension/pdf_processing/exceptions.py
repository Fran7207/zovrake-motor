"""Excepciones del procesamiento documental PDF."""

from __future__ import annotations


class PdfProcessingError(Exception):
    """Error base del procesamiento PDF."""


class PdfInvalidDocumentError(PdfProcessingError):
    """El archivo no es un PDF válido o no puede abrirse."""


class PdfProcessingPageError(PdfProcessingError):
    """Error al procesar una página concreta."""


class PdfExtractionError(PdfProcessingError):
    """Error durante la extracción de contenido."""