"""Excepciones del Document Knowledge Index."""

from __future__ import annotations


class KnowledgeIndexError(Exception):
    """Error base del Document Knowledge Index."""


class InternalModelInputError(KnowledgeIndexError):
    """La entrada no proviene del Internal Document Model Builder."""


class TraceabilityError(KnowledgeIndexError):
    """La trazabilidad con el documento de origen no está preservada."""


class DuplicateIndexEntryError(KnowledgeIndexError):
    """El modelo documental ya está registrado en el índice."""
