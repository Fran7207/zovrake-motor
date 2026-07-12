"""Excepciones del Canonical Representation Engine."""

from __future__ import annotations


class CanonicalEngineError(Exception):
    """Error base del Canonical Representation Engine."""


class ExtractionInputError(CanonicalEngineError):
    """La entrada no proviene del Content Extraction Engine."""


class TraceabilityError(CanonicalEngineError):
    """La trazabilidad con el documento de origen no está preservada."""


class ImmutabilityViolationError(CanonicalEngineError):
    """Intento de modificar una Representación Canónica inmutable."""


class TransformerNotFoundError(CanonicalEngineError):
    """Transformador de sección no registrado."""
