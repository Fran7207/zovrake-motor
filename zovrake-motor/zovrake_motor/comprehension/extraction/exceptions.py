"""Excepciones del Content Extraction Engine."""

from __future__ import annotations


class ExtractionEngineError(Exception):
    """Error base del Content Extraction Engine."""


class ExtractorNotFoundError(ExtractionEngineError):
    """Extractor no registrado."""


class AdapterAccessError(ExtractionEngineError):
    """El documento no fue recibido a través del adaptador documental."""


class OriginalDocumentModifiedError(ExtractionEngineError):
    """El documento original no está preservado."""
