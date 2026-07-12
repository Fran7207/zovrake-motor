"""Excepciones del Internal Document Model Builder."""

from __future__ import annotations


class InternalModelBuilderError(Exception):
    """Error base del Internal Document Model Builder."""


class CanonicalInputError(InternalModelBuilderError):
    """La entrada no proviene del Canonical Representation Engine."""


class TraceabilityError(InternalModelBuilderError):
    """La trazabilidad con el documento de origen no está preservada."""


class ImmutabilityViolationError(InternalModelBuilderError):
    """Intento de modificar un Modelo Documental Interno inmutable."""


class EntityBuilderNotFoundError(InternalModelBuilderError):
    """Constructor de entidad no registrado."""
